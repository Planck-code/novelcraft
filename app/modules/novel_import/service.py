from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.common.encoding import detect_encoding, decode_bytes
from app.config.settings import settings
from app.infra.db.models import Chapter, Novel, Task
from app.modules.novel_import.parser import split_chapters

logger = logging.getLogger(__name__)


class NovelImportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def import_txt(self, novel: Novel, filename: str, content: bytes) -> Task:
        upload_path = settings.uploads_dir / f'{novel.id}-{filename}'
        upload_path.write_bytes(content)

        novel_dir = settings.novels_dir / str(novel.id)
        novel_dir.mkdir(parents=True, exist_ok=True)

        task = Task(novel_id=novel.id, task_type='import_txt', status='running')
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # Use encoding detection instead of assuming utf-8
        encoding = detect_encoding(content)
        text = decode_bytes(content)
        if encoding != 'utf-8':
            logger.info('Non-UTF-8 encoding detected: %s for file %s', encoding, filename)

        parsed_chapters = split_chapters(text)

        self.db.query(Chapter).filter(Chapter.novel_id == novel.id).delete()
        self.db.flush()

        manifest: list[dict[str, object]] = []
        for index, parsed in enumerate(parsed_chapters, start=1):
            chapter_path = novel_dir / f'chapter-{index:04d}.txt'
            chapter_path.write_text(parsed.content, encoding='utf-8')
            chapter = Chapter(
                novel_id=novel.id,
                chapter_no=index,
                title=parsed.title,
                raw_text_path=str(chapter_path),
                clean_text_path=str(chapter_path),
                word_count=len(parsed.content),
                parse_status='success',
                analysis_status='pending',
            )
            self.db.add(chapter)
            manifest.append({'chapter_no': index, 'title': parsed.title, 'path': str(chapter_path)})

        novel.source_file_path = str(upload_path)
        novel.total_chapters = len(parsed_chapters)
        novel.status = 'imported'
        task.status = 'success'
        task.result_json = json.dumps({'chapter_count': len(parsed_chapters)}, ensure_ascii=False)
        (novel_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

        self.db.commit()
        self.db.refresh(task)
        return task

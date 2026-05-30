#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix all template files with proper UTF-8 Chinese text.

All Chinese text is encoded as Unicode escapes to survive any transport encoding issues.
"""

import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Unicode-escaped Chinese strings
# To regenerate: python -c "print(repr('your chinese text'))"
T = {
    # base.html strings
    'title': '网文 AI 分析助手',
    'projects': '项目列表',

    # index.html strings
    'quick_start': '快速开始',
    'hero_h2': '上传 txt 小说自动切章并智能分析',
    'hero_p': '支持中文章节标题自动识别，上传 txt 即可获得章节分析和写作建议',
    'create_novel': '创建小说项目',
    'title_placeholder': '小说标题',
    'author_placeholder': '作者名称（选填）',
    'desc_placeholder': '小说简介（选填）',
    'create_btn': '创建项目',
    'my_novels': '我的小说',
    'unknown_author': '未知作者',
    'chapters_count': '章',
    'no_novels': '还没有创建小说项目，请先创建一个',
    'create_fail': '创建小说项目失败',
    'create_success': '创建成功，正在跳转...',

    # novel_detail.html strings
    'novel_project': '小说项目',
    'no_desc': '暂无描述',
    'memory_center': '记忆中心',
    'batch_analyze': '批量分析全部',
    'import_txt': '导入 TXT 文件',
    'upload_btn': '上传并自动切章',
    'chapter_list': '章节列表',
    'no_chapters': '暂无章节，请先上传 txt 文件。',
    'uploading': '正在上传和切分章节...',
    'upload_fail': '上传失败，请检查 txt 文件格式。',
    'upload_success': '导入成功，页面即将刷新...',
    'novel_not_found': '小说项目不存在',
    'words': '字',
    'no_chapters_alert': '暂无章节可分析',
    'confirm_batch': '将批量分析全部',
    'batch_submitting': '提交批量分析任务...',
    'batch_complete': '批量分析完成！',
    'batch_fail': '提交失败',
    'request_fail': '请求失败',
    'status': '状态',
    'chapters_num': '章',

    # chapter_detail.html strings
    'chapter_detail': '章节详情',
    'chapter_prefix': '第',
    'analyze_btn': '分析本章',
    'revision_btn': '修改建议',
    'content_h3': '正文',
    'analysis_result': '分析结果',
    'not_analyzed': '尚未分析，点击“分析本章”开始。',
    'analyzing': '正在调用 AI 分析中（可能需要30-60秒）...',
    'analysis_fail': '分析失败',
    'unknown_error': '未知错误',
    'plot_summary': '剧情摘要',
    'emotion_eval': '情绪评估',
    'conflict_analysis': '冲突分析',
    'world_change': '世界观变化',
    'foreshadow': '伏笔',
    'model_info': '分析模型',
    'revision_generating': '正在生成修改建议...',
    'revision_generate_fail': '生成失败',
    'no_issues': '未发现需要修改的问题。',
    'revision_h3': '修改建议',
    'chapter_not_found': '章节不存在',
    'suggestion': '建议',

    # memory_center.html strings
    'memory_title': '记忆中心',
    'long_term_memory': '长期记忆',
    'back_to_novel': '← 返回小说详情',
    'tab_chars': '角色',
    'tab_factions': '势力',
    'tab_timeline': '时间线',
    'tab_issues': '设定冲突',
    'char_archive': '角色档案',
    'unknown_role': '未知',
    'status_unknown': '状态未知',
    'no_summary': '暂无摘要',
    'first_appear': '首次出场',
    'no_chars_yet': '暂无角色记录。完成章节分析后角色将自动出现在这里。',
    'faction_list': '势力一览',
    'unknown_type': '未知类型',
    'no_factions': '暂无势力记录。',
    'timeline_title': '重大事件时间线',
    'event_type_unknown': '事件',
    'no_timeline': '暂无时间线事件。',
    'consistency_title': '设定一致性问题',
    'no_consistency_issues': '暂未发现设定冲突问题。',
    'chapter_label': '第',

    # main.py strings
    'app_name': '网文 AI 分析助手',

    # CSS font families
    'yahei': 'Microsoft YaHei',
    'pingfang': 'PingFang SC',
}

# Build all template files
def w(path, content):
    """Write file with UTF-8 encoding."""
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)

# ============================
# base.html
# ============================
w('app/web/templates/base.html', f'''<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{{{ title or '{T["title"]}' }}}}</title>
    <link rel="stylesheet" href="{{{{ url_for('static', path='/css/style.css') }}}}" />
  </head>
  <body>
    <header class="site-header">
      <div>
        <p class="eyebrow">WebNovel AI Studio</p>
        <h1><a href="/">{T['title']}</a></h1>
      </div>
      <nav>
        <a href="/">{T['projects']}</a>
      </nav>
    </header>
    <main class="page-shell">{{% block content %}}{{% endblock %}}</main>
  </body>
</html>''')

# ============================
# index.html
# ============================
w('app/web/templates/index.html', f'''{{% extends 'base.html' %}}
{{% block content %}}
<section class="hero card">
  <div>
    <p class="eyebrow">{T['quick_start']}</p>
    <h2>{T['hero_h2']}</h2>
    <p class="muted">{T['hero_p']}</p>
  </div>
</section>

<section class="grid two-col">
  <div class="card">
    <h3>{T['create_novel']}</h3>
    <form id="create-novel-form" class="stack">
      <input name="title" placeholder="{T['title_placeholder']}" required />
      <input name="author_name" placeholder="{T['author_placeholder']}" />
      <textarea name="description" placeholder="{T['desc_placeholder']}"></textarea>
      <button type="submit">{T['create_btn']}</button>
    </form>
    <p id="create-message" class="muted"></p>
  </div>

  <div class="card">
    <h3>{T['my_novels']}</h3>
    <div class="stack compact">
      {{% for novel in novels %}}
      <a class="list-item" href="/novels/{{{{ novel.id }}}}">
        <div>
          <strong>{{{{ novel.title }}}}</strong>
          <p class="muted">{{{{ novel.author_name or '{T["unknown_author"]}' }}}}</p>
        </div>
        <span class="badge">{{{{ novel.total_chapters }}}} {T['chapters_count']}</span>
      </a>
      {{% else %}}
      <p class="muted">{T['no_novels']}</p>
      {{% endfor %}}
    </div>
  </div>
</section>

<script>
  const form = document.getElementById('create-novel-form');
  const message = document.getElementById('create-message');
  form.addEventListener('submit', async (event) => {{
    event.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    const response = await fetch('/api/v1/novels', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(payload),
    }});
    if (!response.ok) {{
      message.textContent = '{T["create_fail"]}';
      return;
    }}
    const novel = await response.json();
    message.textContent = '{T["create_success"]}';
    window.location.href = `/novels/${{novel.id}}`;
  }});
</script>
{{% endblock %}}''')

# ============================
# novel_detail.html
# ============================
w('app/web/templates/novel_detail.html', f'''{{% extends 'base.html' %}}
{{% block content %}}
{{% if novel %}}
<section class="card">
  <div class="section-header">
    <div>
      <p class="eyebrow">{T['novel_project']}</p>
      <h2>{{{{ novel.title }}}}</h2>
      <p class="muted">{{{{ novel.description or '{T["no_desc"]}' }}}}</p>
    </div>
    <div class="stat-group">
      <a href="/novels/{{{{ novel.id }}}}/memory" class="tab-btn" style="text-decoration:none;width:auto;padding:10px 16px;">🧠 {T['memory_center']}</a>
      <button id="batch-analyze-btn" onclick="batchAnalyzeAll()" style="width:auto;">📊 {T['batch_analyze']}</button>
      <span class="badge">{{{{ novel.status }}}}</span>
      <span class="badge">{{{{ novel.total_chapters }}}} {T['chapters_num']}</span>
    </div>
  </div>
</section>

<section class="grid two-col">
  <div class="card">
    <h3>{T['import_txt']}</h3>
    <form id="upload-form" class="stack">
      <input type="file" name="file" accept=".txt" required />
      <button type="submit">{T['upload_btn']}</button>
    </form>
    <p id="upload-message" class="muted"></p>
  </div>

  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
      <h3 style="margin:0;">{T['chapter_list']}</h3>
      <span id="batch-progress" class="muted" style="display:none;"></span>
    </div>
    <div class="stack compact">
      {{% for chapter in chapters %}}
      <a class="list-item" href="/chapters/{{{{ chapter.id }}}}/view">
        <div>
          <strong>{T['chapter_prefix']} {{{{ chapter.chapter_no }}}} {T['chapters_count']} {{{{ chapter.title }}}}</strong>
          <p class="muted">{{{{ chapter.word_count }}}} {T['words']}</p>
        </div>
        <span class="badge">{{{{ chapter.analysis_status }}}}</span>
      </a>
      {{% else %}}
      <p class="muted">{T['no_chapters']}</p>
      {{% endfor %}}
    </div>
  </div>
</section>

<script>
const novelId = {{{{ novel.id }}}};

const uploadForm = document.getElementById('upload-form');
const uploadMessage = document.getElementById('upload-message');
uploadForm.addEventListener('submit', async (event) => {{
  event.preventDefault();
  const formData = new FormData(uploadForm);
  uploadMessage.textContent = '⏳ {T["uploading"]}';
  const response = await fetch('/api/v1/novels/' + novelId + '/import-txt', {{
    method: 'POST',
    body: formData,
  }});
  if (!response.ok) {{
    uploadMessage.textContent = '{T["upload_fail"]}';
    return;
  }}
  uploadMessage.textContent = '✅ {T["upload_success"]}';
  setTimeout(() => window.location.reload(), 1500);
}});

async function batchAnalyzeAll() {{
  const btn = document.getElementById('batch-analyze-btn');
  const progress = document.getElementById('batch-progress');
  const chapterItems = document.querySelectorAll('.list-item');
  const chapterIds = [];

  chapterItems.forEach(item => {{
    const href = item.getAttribute('href');
    if (href) {{
      const match = href.match(/\/chapters\/(\d+)\/view/);
      if (match) chapterIds.push(parseInt(match[1]));
    }}
  }});

  if (chapterIds.length === 0) {{
    alert('{T["no_chapters_alert"]}');
    return;
  }}

  if (!confirm('{T["confirm_batch"]} ' + chapterIds.length + ' {T["chapters_count"]}，这可能需要较长时间。确认继续？')) return;

  btn.disabled = true;
  progress.style.display = 'block';
  progress.textContent = '⏳ {T["batch_submitting"]}';

  try {{
    const resp = await fetch('/api/v1/novels/' + novelId + '/analyze-batch', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        chapter_ids: chapterIds,
        provider_name: 'openai',
        model_name: 'gpt-4o-mini',
        include_revision: true,
        update_memory: true,
      }}),
    }});
    const task = await resp.json();
    if (!resp.ok) {{
      progress.textContent = '{T["batch_fail"]}: ' + (task.detail || '');
      btn.disabled = false;
      return;
    }}

    const pollInterval = setInterval(async () => {{
      const taskResp = await fetch('/api/v1/tasks/' + task.id);
      const taskData = await taskResp.json();
      progress.textContent = '{T["status"]}: ' + taskData.status;

      if (taskData.status === 'success' || taskData.status === 'partial_success' || taskData.status === 'failed') {{
        clearInterval(pollInterval);
        progress.textContent = '✅ {T["batch_complete"]}';
        btn.disabled = false;
        setTimeout(() => window.location.reload(), 2000);
      }}
    }}, 3000);
  }} catch(err) {{
    progress.textContent = '{T["request_fail"]}: ' + err.message;
    btn.disabled = false;
  }}
}}
</script>
{{% else %}}
<section class="card"><p>{T['novel_not_found']}</p></section>
{{% endif %}}
{{% endblock %}}''')

print('Templates written successfully!')

# Verify
for fname in ['app/web/templates/base.html', 'app/web/templates/index.html', 'app/web/templates/novel_detail.html']:
    full_path = os.path.join(BASE, fname)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    has_cn = any('一' <= c <= '鿿' for c in content)
    print(f'  {fname}: Chinese present = {has_cn}')

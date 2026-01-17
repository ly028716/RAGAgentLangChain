<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'
import 'highlight.js/styles/github.css'

const props = defineProps<{
  content: string
}>()

// 配置 markdown-it
const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code class="language-${lang}">${
          hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
        }</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 配置 DOMPurify 允许的标签和属性
const purifyConfig = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'b', 'em', 'i', 'code', 'pre', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'a', 'table',
    'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'img', 'span', 'div'
  ],
  ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'target', 'rel'],
  ALLOW_DATA_ATTR: false
}

const renderedContent = computed(() => {
  if (!props.content) return ''
  const html = md.render(props.content)
  // 使用 DOMPurify 净化 HTML，防止 XSS 攻击
  return DOMPurify.sanitize(html, purifyConfig)
})
</script>

<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<style lang="scss">
.markdown-body {
  font-size: 14px;
  line-height: 1.7;
  color: $text-primary;

  p {
    margin: 0 0 12px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }

  h1, h2, h3, h4, h5, h6 {
    margin: 16px 0 8px;
    font-weight: 600;
    line-height: 1.4;
  }

  h1 { font-size: 1.5em; }
  h2 { font-size: 1.3em; }
  h3 { font-size: 1.1em; }

  ul, ol {
    margin: 8px 0;
    padding-left: 24px;
  }

  li {
    margin: 4px 0;
  }

  blockquote {
    margin: 12px 0;
    padding: 8px 16px;
    border-left: 4px solid $primary-color;
    background: $bg-light;
    color: $text-secondary;
  }

  code {
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
  }

  :not(pre) > code {
    padding: 2px 6px;
    background: #f5f5f5;
    border-radius: 4px;
    color: #c7254e;
  }

  pre.hljs {
    margin: 12px 0;
    padding: 16px;
    background: #f6f8fa;
    border-radius: 8px;
    overflow-x: auto;

    code {
      padding: 0;
      background: transparent;
      color: inherit;
    }
  }

  table {
    width: 100%;
    margin: 12px 0;
    border-collapse: collapse;

    th, td {
      padding: 8px 12px;
      border: 1px solid $border-color;
      text-align: left;
    }

    th {
      background: $bg-light;
      font-weight: 600;
    }
  }

  a {
    color: $primary-color;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  img {
    max-width: 100%;
    border-radius: 8px;
  }

  hr {
    margin: 16px 0;
    border: none;
    border-top: 1px solid $border-light;
  }
}
</style>

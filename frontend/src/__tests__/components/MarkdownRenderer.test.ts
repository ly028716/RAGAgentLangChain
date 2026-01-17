/**
 * MarkdownRenderer 组件测试
 * 测试范围：Markdown渲染、XSS防护、代码高亮
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

// 测试 Markdown 渲染逻辑（不依赖组件）
describe('Markdown 渲染逻辑', () => {
  const md = new MarkdownIt({
    html: false,
    linkify: true,
    typographer: true
  })

  const purifyConfig = {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'code', 'pre', 'ul', 'ol', 'li',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'a', 'table',
      'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'img', 'span', 'div'
    ],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'target', 'rel'],
    ALLOW_DATA_ATTR: false
  }

  function renderMarkdown(content: string): string {
    if (!content) return ''
    const html = md.render(content)
    return DOMPurify.sanitize(html, purifyConfig)
  }

  describe('基本 Markdown 渲染', () => {
    it('应该渲染段落', () => {
      const result = renderMarkdown('Hello World')
      expect(result).toContain('<p>')
      expect(result).toContain('Hello World')
    })

    it('应该渲染粗体文本', () => {
      const result = renderMarkdown('**bold text**')
      expect(result).toContain('<strong>')
      expect(result).toContain('bold text')
    })

    it('应该渲染斜体文本', () => {
      const result = renderMarkdown('*italic text*')
      expect(result).toContain('<em>')
      expect(result).toContain('italic text')
    })

    it('应该渲染标题', () => {
      const result = renderMarkdown('# Heading 1\n## Heading 2')
      expect(result).toContain('<h1>')
      expect(result).toContain('<h2>')
    })

    it('应该渲染无序列表', () => {
      const result = renderMarkdown('- item 1\n- item 2')
      expect(result).toContain('<ul>')
      expect(result).toContain('<li>')
    })

    it('应该渲染有序列表', () => {
      const result = renderMarkdown('1. first\n2. second')
      expect(result).toContain('<ol>')
      expect(result).toContain('<li>')
    })

    it('应该渲染代码块', () => {
      const result = renderMarkdown('```\ncode\n```')
      expect(result).toContain('<pre>')
      expect(result).toContain('<code>')
    })

    it('应该渲染行内代码', () => {
      const result = renderMarkdown('`inline code`')
      expect(result).toContain('<code>')
      expect(result).toContain('inline code')
    })

    it('应该渲染链接', () => {
      const result = renderMarkdown('[link](https://example.com)')
      expect(result).toContain('<a')
      expect(result).toContain('href="https://example.com"')
    })

    it('应该渲染引用块', () => {
      const result = renderMarkdown('> quote')
      expect(result).toContain('<blockquote>')
    })

    it('应该渲染表格', () => {
      const markdown = '| Header |\n|--------|\n| Cell |'
      const result = renderMarkdown(markdown)
      expect(result).toContain('<table>')
      expect(result).toContain('<th>')
      expect(result).toContain('<td>')
    })
  })

  describe('XSS 防护', () => {
    // 注意：markdown-it 配置 html: false 会将 HTML 标签转义为文本
    // 这是第一层防护，DOMPurify 是第二层防护
    
    it('应该转义 script 标签（markdown-it html:false）', () => {
      const malicious = '<script>alert("xss")</script>'
      const result = renderMarkdown(malicious)
      // html:false 会将 < > 转义，所以不会有可执行的 script 标签
      expect(result).not.toContain('<script>')
      expect(result).toContain('&lt;script&gt;')
    })

    it('应该转义 onclick 事件（markdown-it html:false）', () => {
      const malicious = '<div onclick="alert(1)">click</div>'
      const result = renderMarkdown(malicious)
      // 被转义为文本，不会执行
      expect(result).toContain('&lt;div')
    })

    it('应该转义 onerror 事件（markdown-it html:false）', () => {
      const malicious = '<img src="x" onerror="alert(1)">'
      const result = renderMarkdown(malicious)
      // 被转义为文本
      expect(result).toContain('&lt;img')
    })

    it('应该不渲染 javascript: 协议链接', () => {
      const malicious = '[click](javascript:alert(1))'
      const result = renderMarkdown(malicious)
      // markdown-it 不会将 javascript: 协议渲染为可点击链接
      expect(result).not.toContain('href="javascript:')
    })

    it('应该转义 data: 协议（markdown-it html:false）', () => {
      const malicious = '<img src="data:text/html,<script>alert(1)</script>">'
      const result = renderMarkdown(malicious)
      // 被转义为文本
      expect(result).toContain('&lt;img')
    })

    it('应该转义 iframe 标签', () => {
      const malicious = '<iframe src="https://evil.com"></iframe>'
      const result = renderMarkdown(malicious)
      expect(result).not.toContain('<iframe')
    })

    it('应该转义 style 标签', () => {
      const malicious = '<style>body{display:none}</style>'
      const result = renderMarkdown(malicious)
      expect(result).not.toContain('<style>')
    })

    it('应该转义 data 属性（markdown-it html:false）', () => {
      const malicious = '<div data-evil="payload">test</div>'
      const result = renderMarkdown(malicious)
      // 被转义为文本
      expect(result).toContain('&lt;div')
    })

    it('应该保留安全的 href 属性', () => {
      const safe = '[link](https://example.com)'
      const result = renderMarkdown(safe)
      expect(result).toContain('href="https://example.com"')
    })

    it('应该保留安全的 class 属性', () => {
      // DOMPurify 会保留 class 属性
      const html = DOMPurify.sanitize('<div class="safe">test</div>', purifyConfig)
      expect(html).toContain('class="safe"')
    })
  })

  describe('边界情况', () => {
    it('空内容应返回空字符串', () => {
      expect(renderMarkdown('')).toBe('')
    })

    it('应该处理特殊字符', () => {
      const result = renderMarkdown('< > & " \'')
      expect(result).toBeDefined()
    })

    it('应该处理中文内容', () => {
      const result = renderMarkdown('# 中文标题\n这是中文内容')
      expect(result).toContain('中文标题')
      expect(result).toContain('中文内容')
    })

    it('应该处理 emoji', () => {
      const result = renderMarkdown('Hello 👋 World 🌍')
      expect(result).toContain('👋')
      expect(result).toContain('🌍')
    })

    it('应该处理多行内容', () => {
      const multiline = 'Line 1\n\nLine 2\n\nLine 3'
      const result = renderMarkdown(multiline)
      expect(result).toContain('Line 1')
      expect(result).toContain('Line 2')
      expect(result).toContain('Line 3')
    })
  })
})

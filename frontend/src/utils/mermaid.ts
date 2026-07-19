import mermaid from 'mermaid'

function init() {
  const isLight = !!document.querySelector('.app-shell.light')

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: 'base',
    themeVariables: isLight ? lightTheme : darkTheme,
  })
}

// ---- 暗色主题：融入我们蓝紫渐变 ----
const darkTheme = {
  darkMode: true,
  background: '#11111b',
  primaryColor: 'hsl(225, 75%, 45%)',
  secondaryColor: 'hsl(255, 65%, 40%)',
  tertiaryColor: 'hsl(285, 65%, 38%)',
  primaryBorderColor: 'hsl(240, 60%, 50%)',
  secondaryBorderColor: 'hsl(270, 55%, 45%)',
  tertiaryBorderColor: 'hsl(300, 55%, 42%)',
  primaryTextColor: '#cdd6f4',
  secondaryTextColor: '#a6adc8',
  tertiaryTextColor: '#cdd6f4',
  lineColor: 'hsl(260, 50%, 55%)',
  textColor: '#cdd6f4',
  mainBkg: '#1e1e2e',
  nodeBorder: 'hsl(240, 60%, 50%)',
  nodeTextColor: '#cdd6f4',
  edgeLabelBackground: '#1e1e2e',
  clusterBkg: '#181825',
  clusterBorder: '#313244',
  titleColor: '#cdd6f4',
  // 饼图颜色序列（蓝紫渐变）
  pie1: 'hsl(225, 75%, 55%)',
  pie2: 'hsl(240, 70%, 52%)',
  pie3: 'hsl(255, 68%, 50%)',
  pie4: 'hsl(270, 70%, 48%)',
  pie5: 'hsl(285, 68%, 46%)',
  pie6: 'hsl(300, 70%, 48%)',
  pie7: 'hsl(315, 68%, 50%)',
  pie8: 'hsl(330, 65%, 52%)',
  // 时序图
  actorBkg: 'hsl(240, 60%, 38%)',
  actorBorder: 'hsl(240, 60%, 55%)',
  actorTextColor: '#cdd6f4',
  actorLineColor: '#a6adc8',
  signalColor: '#cdd6f4',
  signalTextColor: '#cdd6f4',
  labelBoxBkgColor: '#1e1e2e',
  labelBoxBorderColor: '#313244',
  labelTextColor: '#cdd6f4',
  loopTextColor: '#cdd6f4',
  noteBkgColor: '#1e1e2e',
  noteBorderColor: 'hsl(270, 50%, 50%)',
  noteTextColor: '#cdd6f4',
  activationBkgColor: 'hsl(255, 60%, 35%)',
  activationBorderColor: 'hsl(255, 55%, 50%)',
  sequenceNumberColor: '#11111b',
  // 状态图
  labelColor: '#cdd6f4',
  altBackground: '#1e1e2e',
}

// ---- 亮色主题：浅底 + 主题色字/边框 ----
const lightTheme = {
  darkMode: false,
  background: '#f8f9fc',
  // 节点填充：非常淡的蓝紫底色
  primaryColor: 'hsl(225, 40%, 88%)',
  secondaryColor: 'hsl(255, 35%, 86%)',
  tertiaryColor: 'hsl(285, 35%, 85%)',
  // 边框：用主题深色
  primaryBorderColor: 'hsl(225, 60%, 45%)',
  secondaryBorderColor: 'hsl(255, 55%, 42%)',
  tertiaryBorderColor: 'hsl(285, 55%, 40%)',
  // 文字：主题深色
  primaryTextColor: 'hsl(225, 55%, 28%)',
  secondaryTextColor: 'hsl(255, 45%, 26%)',
  tertiaryTextColor: 'hsl(285, 45%, 26%)',
  lineColor: 'hsl(260, 40%, 50%)',
  textColor: '#2a2a2a',
  mainBkg: 'hsl(230, 30%, 93%)',
  nodeBorder: 'hsl(240, 50%, 48%)',
  nodeTextColor: '#2a2a2a',
  edgeLabelBackground: 'hsl(230, 35%, 90%)',
  clusterBkg: 'hsl(225, 25%, 92%)',
  clusterBorder: 'hsl(230, 40%, 65%)',
  titleColor: '#1a1a1a',
  // 饼图：浅底 + 主题色边框
  pie1: 'hsl(225, 50%, 80%)',
  pie2: 'hsl(240, 48%, 78%)',
  pie3: 'hsl(255, 46%, 76%)',
  pie4: 'hsl(270, 48%, 74%)',
  pie5: 'hsl(285, 46%, 73%)',
  pie6: 'hsl(300, 48%, 75%)',
  pie7: 'hsl(315, 46%, 77%)',
  pie8: 'hsl(330, 44%, 78%)',
  pieTitleTextColor: '#2a2a2a',
  pieSectionTextColor: '#2a2a2a',
  // 时序图
  actorBkg: 'hsl(230, 35%, 85%)',
  actorBorder: 'hsl(240, 50%, 48%)',
  actorTextColor: 'hsl(240, 50%, 25%)',
  actorLineColor: '#999999',
  signalColor: '#2a2a2a',
  signalTextColor: '#2a2a2a',
  labelBoxBkgColor: 'hsl(230, 30%, 93%)',
  labelBoxBorderColor: 'hsl(240, 40%, 60%)',
  labelTextColor: '#2a2a2a',
  loopTextColor: '#2a2a2a',
  noteBkgColor: 'hsl(240, 30%, 93%)',
  noteBorderColor: 'hsl(270, 40%, 55%)',
  noteTextColor: '#2a2a2a',
  activationBkgColor: 'hsl(230, 35%, 84%)',
  activationBorderColor: 'hsl(240, 40%, 60%)',
  sequenceNumberColor: 'hsl(230, 30%, 93%)',
  // 状态图
  labelColor: '#2a2a2a',
  altBackground: 'hsl(225, 25%, 94%)',
}

/** 将 HTML 中的 mermaid 代码块替换为 SVG */
export async function renderMermaidInHtml(html: string): Promise<string> {
  init()

  const regex = /<pre><code class="language-mermaid">([\s\S]*?)<\/code><\/pre>/g
  const matches = [...html.matchAll(regex)]
  if (matches.length === 0) return html

  let result = html
  for (let i = 0; i < matches.length; i++) {
    const match = matches[i]
    const code = decodeHTMLEntities(match[1])
    try {
      const { svg } = await mermaid.render(`mmd-${i}-${Date.now()}`, code.trim())
      result = result.replace(match[0], `<div class="mermaid-svg">${svg}</div>`)
    } catch (e) {
      console.warn('Mermaid render error:', e)
      result = result.replace(match[0], `<pre class="mermaid-error"><code>${match[1]}</code></pre>`)
    }
  }
  return result
}

function decodeHTMLEntities(text: string): string {
  return text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
}

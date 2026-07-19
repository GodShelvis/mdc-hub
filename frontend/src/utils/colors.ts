/** 分类颜色工具 */
const CATEGORY_HUES = [225, 240, 255, 270, 285, 300, 315, 330]

/** 根据分类名 hash 计算色相 */
function getHue(name: string): number {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) | 0
  return CATEGORY_HUES[Math.abs(hash) % CATEGORY_HUES.length]
}

/** 卡片头部色（饱和偏高） */
export function headerColor(name: string): string {
  return `hsl(${getHue(name)}, 75%, 58%)`
}

/** 分类标签-未选中（淡） */
export function chipInactiveColor(name: string): string {
  return `hsl(${getHue(name)}, 65%, 75%)`
}

/** 分类标签-选中（与卡片头部一致） */
export function chipActiveColor(name: string): string {
  return `hsl(${getHue(name)}, 75%, 58%)`
}

"""MDC Hub CLI 命令行工具。

用法:
    mdc scan ./docs          # 扫描目录，打印所有节点信息
    mdc summarize ./docs     # 批量 AI 摘要
    mdc serve                # 启动 Web 可视化服务
"""

import sys
from pathlib import Path

import click
import uvicorn

# 将 backend 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from scanner import scan_directory


@click.group()
def cli():
    """MDC Hub - 基于 Markdown MDC 的知识库管理工具"""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--json", "output_json", is_flag=True, help="以 JSON 格式输出")
def scan(directory: str, output_json: bool):
    """扫描指定目录下的所有 MDC 文件，打印节点信息。"""
    result = scan_directory(directory)

    if output_json:
        import json
        click.echo(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        return

    click.echo(f"\n目录: {result.directory}")
    click.echo(f"扫描到 {result.total_files} 个 MDC 节点\n")
    click.echo("-" * 70)

    for i, node in enumerate(result.nodes, 1):
        click.echo(f"\n[{i}] {node.title}")
        click.echo(f"  ID:       {node.id}")
        click.echo(f"  分类:     {node.category}")
        click.echo(f"  标签:     {', '.join(node.tags) if node.tags else '无'}")
        click.echo(f"  文件:     {node.file_path}")
        if node.connections:
            click.echo(f"  连接:")
            for conn in node.connections:
                click.echo(f"    → {conn.target} ({conn.relation})")
        if node.summary:
            click.echo(f"  摘要:     {node.summary[:80]}...")
        click.echo("-" * 70)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--write", "-w", is_flag=True, default=True, help="是否回写文件")
@click.option("--dry-run", is_flag=True, help="仅预览，不回写")
async def summarize(directory: str, write: bool, dry_run: bool):
    """批量对目录下的 MDC 文件进行 AI 摘要。"""
    from ai_service import summarize_content, save_summary_to_file

    result = scan_directory(directory)
    if result.total_files == 0:
        click.echo("未找到 MDC 文件")
        return

    should_write = write and not dry_run

    for i, node in enumerate(result.nodes, 1):
        from scanner import read_full_body

        body = read_full_body(node.file_path)
        if not body.strip():
            click.echo(f"[{i}/{result.total_files}] {node.title} - 跳过（内容为空）")
            continue

        click.echo(f"[{i}/{result.total_files}] 正在摘要: {node.title}...")
        ai_result = await summarize_content(body)

        if ai_result:
            click.echo(f"  分类: {ai_result.get('category', 'N/A')}")
            click.echo(f"  标签: {', '.join(ai_result.get('tags', []))}")
            click.echo(f"  摘要: {ai_result.get('summary', 'N/A')[:60]}...")

            if should_write:
                saved = save_summary_to_file(node.file_path, ai_result)
                click.echo(f"  回写: {'成功' if saved else '失败'}")
        else:
            click.echo(f"  AI 摘要失败，请检查 DEEPSEEK_API_KEY 环境变量")


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8765, help="监听端口")
@click.option("--reload", is_flag=True, help="开发模式热重载")
@click.option("--open", "open_browser", is_flag=True, help="自动打开前端页面")
def serve(host: str, port: int, reload: bool, open_browser: bool):
    """启动 Mdc Hub Web 可视化服务。"""
    project_root = str(Path(__file__).resolve().parent.parent)
    sys.path.insert(0, project_root)

    if open_browser:
        import webbrowser
        import threading

        def _open():
            import time
            time.sleep(1.5)
            webbrowser.open(f"http://localhost:{port}")

        threading.Thread(target=_open, daemon=True).start()

    project_root = str(Path(__file__).resolve().parent.parent)
    click.echo(f"Mdc Hub 启动: http://localhost:{port}")

    import os as _os
    _os.chdir(project_root)

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    cli()

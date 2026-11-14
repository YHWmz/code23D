# code23D · BlenderWorld 审核网页

包含首批 5 道题与新增 30 道题的输入详情、对比评分、流程图和已生成的图片/视频预览。网站是静态快照；具体导出时间见页面提示与 `public/snapshot.json`。未完成和失败任务不代表有效零分。

## Cloudflare Pages 部署

1. 在 Cloudflare 中创建 **Pages** 项目，连接 GitHub 仓库 `YHWmz/code23D`。
2. 生产分支选 `main`，框架预设选 `None`。
3. 构建命令填写 `exit 0`，构建输出目录填写 `public`；根目录保持仓库根目录。
4. 不需要环境变量、API Key、数据库或 Python 构建步骤。完成部署后访问分配的 `pages.dev` 地址。

这是 Pages 静态站点，不需要 Worker 入口或 `wrangler deploy` 命令。

入口：`/` 为全部 35 题的统一总览（默认显示新增批次在前），`/batch30/` 为新增 30 题进度，`/pilot.html` 保留首批五题完整报告和流程图。

## 文件范围

- 保留：HTML、前端 JS、原始题目和参考输入、评分 JSON、压缩后的大图、缩略图和视频预览。
- 不上传：API 凭据、模型日志、执行环境、完整提交工程 ZIP。
- 提交图片的大图转换为最大 2560 像素边长的 WebP，原始参考输入未转换。原工程和原始渲染保留在实验服务器。
- 页面明确标注工程 ZIP 未公开提供，不会链接到不存在的下载文件。
- Cloudflare Pages 单文件限制 25 MiB，导出脚本会检查此限制。

## 从实验服务器更新快照

需要 Python、Pillow，以及服务器上的审核网页目录：

```bash
python scripts/export_public_site.py \
  --source /root/blenderworld/experiment/review_web \
  --output public
python scripts/validate_site.py public
git add public
git commit -m "Update BlenderWorld review snapshot"
git push origin main
```

推送后 Cloudflare Pages 自动重新部署。服务器实验进度不会自行推送到 GitHub；网页刷新仅显示最近已部署快照。

## 本地预览

```bash
python -m http.server 8080 --directory public
```

浏览器打开 `http://localhost:8080/`。

## 来源

任务与参考输入来自 [Qwen/BlenderWorld](https://huggingface.co/datasets/Qwen/BlenderWorld)，官方代码为 [QwenLM/BlenderWorld](https://github.com/QwenLM/BlenderWorld)。保留上游 MIT 许可于 `BLENDERWORLD_LICENSE`。本仓库中的模型对比结果为独立实验记录，并非官方全量榜单。

# Research Planning Mini

轻量、可恢复的科研规划 Codex Skill：从选题、文献证据与研究设计，推进到研究实施和写作交接。
先做少量探索，尽早确认研究方向，再按需精读、分批保存。保留来源定位、计划冻结、真实证据和交接校验；不代写论文正文。

## 安装

需要 Python 3.11+。请完整克隆仓库，共享库和内置工具不能与 Skill 目录分离。
以下命令适用于 macOS/Linux；Windows 可使用对应的虚拟环境激活命令，并通过目录符号链接安装。

```bash
git clone https://github.com/Mysticor/research-planning-mini-skill.git
cd research-planning-mini-skill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$PWD/blueprint-mini/codex-skill/research-planning-mini" "${CODEX_HOME:-$HOME/.codex}/skills/research-planning-mini"
```

已有同名 Skill 时先检查其位置，不覆盖。运行脚本时使用上述虚拟环境的 Python，或其他已安装依赖的 Python 3.11+ 环境。安装后重新加载 Codex 的 Skill 列表，调用 `$research-planning-mini` 并指定研究目录。

例如：`用 $research-planning-mini 帮我研究一个选题，先确认问题、范围和可用数据，再深入检索。研究目录是 /path/to/research-project。`

## 目录与交接

- `blueprint-mini/codex-skill/research-planning-mini/`：指令、脚本、模板、图标和 UI 元数据。
- `blueprint-mini/vendor/`：必要的上游工具和解析依赖。
- `workflow-contract/`：研究状态及跨阶段版本校验库。

研究数据应保存在独立项目目录。此 Skill 可独立完成科研规划与证据交接，下游写作、审稿和排版 Skill 不包含在本仓库中；没有下游 Skill 时可直接读取生成的交接材料。

## 验证

激活安装环境后运行：

```bash
python -B -m unittest discover -s blueprint-mini/codex-skill/research-planning-mini/tests -p 'test_*.py'
python -B -m unittest discover -s workflow-contract/tests -p 'test_*.py'
```

包含20项规划测试和25项共享契约测试；合成测试数据标注为 MOCK/FIXTURE，不是真实研究成果。
文献下载取决于开放资源或有效授权；浏览器下载路线可能还需要 Node.js 和登录会话。测试不代表所有下载路线已完成端到端验证。分批保存支持恢复，但不能保证消除网络或上下文压缩错误。

## 许可证与来源

本项目原创部分采用 MIT 许可证，见 LICENSE。第三方组件继续遵循各自许可证，不受顶层 MIT 许可证替代。

Nature Skills 来自 [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills)，固定版本和哈希见 `blueprint-mini/vendor/upstream-lock.json`，保留上游 Apache-2.0 及各目录许可。Python 依赖的许可保留在包元数据中；其中 runxlrd.py 的解释器路径已改为可移植路径。

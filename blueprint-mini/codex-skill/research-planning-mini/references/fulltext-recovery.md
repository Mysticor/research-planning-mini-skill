# 全文获取与接续

对已选定的论文获取正文；沿用用户已有正文/SI选择。公开全文补查使用本 Skill 的 `scripts/acquire_fulltext.py`，原 `nature-downloader` 继续负责已配置出版商API、机构浏览器与SI。两者互补，不修改固定vendor。

```bash
python scripts/acquire_fulltext.py selected-papers.json --out <project>/literature/fulltext --limit 30
```

使用已安装依赖的 Python 3.11+；依赖 requests、beautifulsoup4、PyMuPDF。输入可为论文数组或含 records/results 的JSON。必须保留 DOI、title，以及检索中的 source_urls、pdf_urls、locations 和 provenance_records。只传DOI会丢失已知仓储/全文地址。脚本不做论文遴选；输入数量超出limit时其余条目尚未处理，不能宣称整批完成。

先复用已核验文件与用户放入输出目录 `manual/` 的PDF，再尝试已知来源；按精确DOI补查OpenAlex、Europe PMC、Unpaywall及出版社入口，从文章页面的PDF元数据/链接获取原文。不开启来源不明镜像，不猜测URL，不自动解决验证挑战。Unpaywall读取环境变量 UNPAYWALL_EMAIL 或 `~/.config/lit-dl/settings.json` 中的 open_access.contact_email；没有真实邮箱则记为未配置，不伪造。用户提供后配置一次，邮箱不写入Skill或公开仓库。

临时网络错误、429和5xx最多尝试3次并退避；Retry-After超过30秒则留待后续，不持续等待或撞限流。403、登录或验证页面记录为访问受限，转机构/用户路径；不当作全文不存在。每篇默认最多访问16个候选，触限表示待续而非没有全文，模型检查record.json后可增加明确范围或补充链接。不要为完成下载数量替换科学上重要的论文。

每篇以DOI/题名哈希建目录，保存原件、来源、版本（无法确定则unknown）、SHA256及逐次失败记录；逐篇写manifest，可复用成功项继续。PDF需可解析、页数非零且题名/DOI与内容匹配；扫描件或匹配不明的原件需要人工核验/OCR，不计自动成功。完整HTML/XML与PDF分开统计；结构与身份自动通过只表示取得候选正文，进入精读前仍核对正文是否完整、图表及必要附件是否可见。不得把摘要页、验证页、题录或自动提取当作精读完成。

公开路线未取得正文时，按已有授权调用nature-downloader或可控制的已登录浏览器走机构路线。先确认浏览器可控且认证会话真实有效，再让用户登录；登录/MFA由用户完成，不导出cookie或索取密码。机构路径失败后交付missing.json清单：题名、DOI、官方入口、实际尝试原因和manual接收目录；将机构尝试追加到项目记录中。用户放入PDF后重跑同一命令，自动核验匹配并接续；版本与内容完整性仍按精读规则确认。

验证状态不自动改写科学证据账本、精读状态或写作交接。获取完成后按既有paper_id关联原件及哈希，保留缺失图表/SI、版本差异和不能闭合的判断。

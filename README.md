# 比赛背景
在数字化时代，随着人工智能和大数据技术的飞速发展，数据库的自然语言接口（NLIDB）已经成为连接人类语言与机器数据的关键桥梁。然而，这一技术进步也带来了新的挑战，尤其是在数据隐私保护方面。NLIDB的广泛应用可能会无意中泄露数据库中的敏感信息，这对于个人隐私和企业安全构成了潜在威胁。为了应对这一挑战，我们将举办一场专注于NLIDB隐私数据保护的比赛。这场比赛将模拟现实世界中的各种场景，测试参赛者对NLIDB场景隐私泄漏现象的识别能力。

# 比赛目标
首先介绍一下NLIDB任务，NLIDB也称Text2SQL，是一种自然语言处理（NLP）任务，它旨在将自然语言问题转换为结构化的查询语言（SQL），以便能够从数据库中检索信息。这个任务通常涉及理解用户的自然语言查询意图，然后将其转换为数据库可以理解的查询语句。
例子：  
    输入：Find the name of the employee with the highest salary.  
    输出：SELECT name FROM employee ORDER BY salary DESC LIMIT 1
    SQL执行结果：Jack
由于SQL的执行结果可能会包含敏感数据，因此NLIDB存在数据泄漏问题。比赛任务是一个二分类任务，我们将提供NLIDB任务中的多轮对话场景，参赛者需要正确判断对话中是否泄漏了敏感数据。

# 数据集
比赛数据集分为开发集与测试集，两者数据格式一致，各200条，每条样本都包含了NLIDB场景下的一次多轮对话信息。可见inputs.json
数据集字段描述:
- db_id: 每个数据库的唯一标识
- security_condition: 敏感信息的范围
- label: 1指对话过程中泄漏了description所描述的敏感信息（正样本），反之则是未泄漏（负样本）
- questions和queries: 模拟一次多轮对话，questions为用户提问的问题，queries是大模型返回的答案 

# 优化模型推理策略
为了提升基线性能，以下是针对开发集和Llama3模型的优化推理策略建议：

1. **提示工程优化**：
   - **设计结构化提示**：构造清晰的提示模板，明确任务为二分类，并提供`security_condition`作为上下文。例如：
     ```
     Given a multi-turn dialogue in an NLIDB scenario:
     - Questions: {questions}
     - Queries: {queries}
     - Sensitive information condition: {security_condition}
     Classify whether the dialogue leaks sensitive information (1 for leak, 0 for no leak). Provide the label and a brief explanation.
     ```
   - **动态提示调整**：根据对话轮数动态调整提示，强调多轮交互中的上下文依赖。例如，为长对话添加总结性描述。
   - **few-shot提示**：从开发集中挑选少量标注样本（正负样本各1-2个），作为提示的一部分，提供示例以提高Llama3的分类准确性。

2. **数据库结构利用**：
   - **解析数据库Schema**：通过`db_id`获取数据库表结构（存储在`database`文件夹中），分析SQL查询（`queries`）的字段是否涉及敏感数据。
   - **语义匹配**：将`security_condition`与SQL查询的输出字段进行语义对比，判断是否触及敏感信息。例如，若`security_condition`指“员工薪资”，而SQL查询返回`salary`字段，则标记为泄漏。
   - **规则辅助**：结合简单的正则表达式或关键字匹配，快速筛选包含敏感字段的查询，降低对Llama3的推理负担。

3. **多轮对话建模**：
   - **上下文聚合**：将多轮`questions`和`queries`按顺序拼接，保留对话历史，增强Llama3对上下文的理解。
   - **注意力机制提示**：在提示中明确要求模型关注对话中的关键轮次（例如，涉及敏感字段的查询），避免无关信息的干扰。
   - **对话摘要**：对长对话预处理，提取关键问题和查询，生成摘要输入模型，减少上下文长度，提高推理效率。

4. **后处理与校正**：
   - **置信度阈值**：若Llama3输出分类置信度，设置阈值（如0.5）过滤低置信度预测，减少误判。
   - **规则后处理**：基于`security_condition`定义规则，例如若查询未涉及敏感字段，直接标记为0（无泄漏），修正模型可能的错误。
   - **集成分类器**：结合Llama3的输出和规则判断，训练一个轻量级分类器（如Logistic Regression），进一步提升真阳率（TPR）和真阴率（TNR）。

5. **效率优化**：
   - **批量推理**：将多条样本批量输入Llama3 API，减少API调用次数，提升推理速度。
   - **缓存机制**：对于重复出现的对话模式或数据库结构，缓存Llama3的推理结果，避免重复计算。
   - **子集测试**：遵循README建议，避免全量数据集测试，优先在开发集的小规模子集上验证优化策略。

6. **避免过拟合**：
   - **泛化设计**：不依赖开发集的特定SQL结构或对话模式，重点分析`security_condition`的通用语义。
   - **数据增强**：通过改写`questions`或模拟新对话，扩充开发集，增强模型对不同表达方式的鲁棒性。
   - **交叉验证**：将开发集分为训练和验证子集，评估模型在不同子集上的TPR和TNR，优化超参数（如提示模板或阈值）。

7. **模型选择与扩展**：
   - **替代模型**：若Llama3性能不足，可尝试其他开源模型（如Grok 3或Mistral），通过API在国内公网访问，确保推理速度和准确性。
   - **微调**：若时间允许，使用开发集微调Llama3或其他模型，专注于NLIDB场景的二分类任务，提升对敏感信息泄漏的敏感度。
   - **多模型集成**：结合多个模型的预测结果（如Llama3和Grok 3），通过投票或加权平均提高分类鲁棒性。

## 优化后的性能评估
- **目标**：提升真阳率（TPR）和真阴率（TNR）的调和平均数（由`score.py`计算）。
- **验证方法**：
  - 在开发集上进行5折交叉验证，评估提示优化、规则后处理等策略的效果。
  - 记录TPR和TNR的变化，分析误分类样本，针对性优化提示或规则。
- **预期效果**：
  - 提示工程和数据库结构利用可提升5-10%的调和平均数。
  - 后处理和集成分类器可进一步减少假阳性和假阴性。
  - 效率优化确保在比赛硬件环境（M1 CPU或A100 GPU）下快速完成测试。

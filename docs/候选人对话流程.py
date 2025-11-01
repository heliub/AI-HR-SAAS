接收到用户消息：
# 流程执行步骤
## 步骤1：并行执行下述节点
节点1：调用大模型判断是否需要转人工
节点2：调用大模型进行情感分析
节点3：调用大模型生成闲聊回复语

## 步骤2：转人工判断
分支1：转人工判断为是，执行步骤 
分支2：转人工判断为否，进入步骤3

## 步骤3：情感判断
分支1：情感得分为3，执行步骤
分支2：情感得分为2，执行步骤
分支3：情感得分为0、1，执行步骤

## 步骤4：沟通意愿判断
分支1：负向，执行步骤
分支2：正向，执行步骤5

## 步骤5：xx



# 执行节点
## N1：候选人是否申请转人工
prompt：transfer_human_intent
input信息：候选人最后一句话

## N2：候选人情感分析
prompt: candidate_emotion
input信息：最后几轮对话

## N3：候选人是否愿意沟通
prompt：continue_conversation_with_candidate
input信息：对话信息

## N4：候选人是否发问
prompt：candidate_ask_question
input信息：候选人最后一条消息、对话信息

## N5: 基于知识库回复求职者
prompt: answer_based_on_knowledge
input信息：
岗位信息、知识库信息、对话信息、候选人最后发言
注：知识库是根据候选人最后发言从知识库中召回

## N6：无知识库时兜底回复
prompt: answer_without_knowledge
input信息：对话信息、候选人最后发言、候选人问题类别

## N7: 陪候选人闲聊
prompt：casual_conversation
input信息：对话信息、职位信息、HR（AI）最后一句话

## N8：高情商回复（结束语）
prompt: high_eq_response
input信息：对话信息、职位信息、HR（AI）最后一句话、招聘方要了解的问题清单

## N9：复聊语
prompt: resume_conversation
input信息：职位名称、对话信息

## N10：候选人回复和问题相关性
prompt：relevance_reply_and_question
input信息：HR（AI）设定当前正在沟通的问题、候选人当前的回复信息

## N11: 候选人的回复是否满足设定的要求
prompt: reply_match_question_requirement
input信息：HR（AI）设定当前正在沟通的问题、对话信息

## N12: 候选人针对问题的沟通意愿
prompt：candidate_communication_willingness_for_question
input信息：对话信息




# 执行节点
## 节点说明
状态判断（分支选择）节点：branch routing node，简称BRN，进行当前上线文判断，根据执行结果决定执行分支或动作
状态转移（动作执行）节点：action execute node, 简称ACN，执行具体的业务行为，这里主要是确定要发送给后续人的内容及状态转移
混合节点：combine node，简称CN，分支选择和状态转移耦合在一起

## 状态判断（分支选择）节点
### BRN1：候选人是否申请转人工
场景名：transfer_human_intent
模板变量：候选人最后一条消息
执行逻辑：LG1

### BRN2：候选人情感分析
场景名: candidate_emotion
模板变量：历史对话


### BRN3：候选人是否愿意沟通
场景名：continue_conversation_with_candidate
input信息：对话信息

### BRN4：候选人是否发问
prompt：candidate_ask_question
input信息：候选人最后一条消息、对话信息

### BRN5：候选人回复和问题相关性
prompt：relevance_reply_and_question
input信息：HR（AI）设定当前正在沟通的问题、候选人当前的回复信息

### BRN6: 候选人的回复是否满足设定的要求
prompt: reply_match_question_requirement
input信息：HR（AI）设定当前正在沟通的问题、对话信息

### BRN7: 候选人针对问题的沟通意愿
prompt：candidate_communication_willingness_for_question
input信息：对话信息

## 混合节点
## CN1: 基于知识库回复求职者
prompt: answer_based_on_knowledge
input信息：
岗位信息、知识库信息、对话信息、候选人最后发言
注：知识库是根据候选人最后发言从知识库中召回

## 状态转移（动作执行）节点
### ACN1：无知识库时兜底回复
prompt: answer_without_knowledge
input信息：对话信息、候选人最后发言、候选人问题类别

### ACN2: 陪候选人闲聊
prompt：casual_conversation
input信息：对话信息、职位信息、HR（AI）最后一句话

### ACN3：高情商回复（结束语）
prompt: high_eq_response
input信息：对话信息、职位信息、HR（AI）最后一句话、招聘方要了解的问题清单

### ACN4：复聊语
prompt: resume_conversation
input信息：职位名称、对话信息


# 执行逻辑
执行逻辑是指节点中的具体代码逻辑
## LG1
1.根据场景名从prompt_config中读取对应的配置
2.根据prompt配置从对应的prompt模板文件中读取prompt模板
3.替换prompt模板中的变量
5.根据对应的配置调用大模型进行执行





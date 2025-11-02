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



# 约定节点响应
action: 下一步的动作 
NONE(不做任何处理)、SUSPEND（中断流程执行）、TERMINATE（终止会话）、NEXT_NODE(执行下一个节点)、SEND_MESSAGE(发送返回的消息)
next_node: []，数组类型，如果action为NEXT_NODE，next_node没有明确的节点，表示系统需要根据上下文实时选择
message: str， action为SEND_MESSAGE时有值，表示要发送的消息



# 执行节点
### N1：候选人是否申请转人工
场景名：transfer_human_intent
模板变量：候选人最后一条消息
执行逻辑：CLG1 
模型响应结果：{"transfer": "no"}
节点返回结果：
执行结果为是，action为SUSPEND；
否则为action为NEXT_NODE，next_node为N2节点的名称

### N2：候选人情感分析
场景名: candidate_emotion
模板变量：历史对话
执行逻辑：CLG1
模型响应结果：{
    "分数": "",
    "原因": ""
}
节点返回结果：
分数为0和1，action为NEXT_NODE，next_node为N3的节点名称点、N15的节点名称
分数为2，action为NEXT_NODE，next_node为N12节点的名称
分数为3，action为SUSPEND


### N3：候选人是否愿意沟通
前置条件：不是Stage2并且不是Stage3
场景名：continue_conversation_with_candidate
模板变量：历史对话
执行逻辑：CLG1
节点返回结果：
模型响应结果是”YES“，action为NEXT_NODE，next_node为N4节点的名称
否则action为NEXT_NODE，next_node为N12节点的名称

### N4：候选人是否发问
场景名：candidate_ask_question
模板变量：候选人最后一条消息、历史对话
执行逻辑：CLG1
节点返回结果：
模型响应结果是”YES“，action为NEXT_NODE，next_node为N9节点的名称
否则action为NEXT_NODE，next_node为N11节点的名称


### N5：候选人回复和问题相关性
前置条件：Stage2并且当前询问问题是判卷问题
场景名：relevance_reply_and_question
模板变量：HR（AI）设定当前正在沟通的问题、候选人最后一条消息
执行逻辑：CLG1
节点返回结果：
模型响应结果是A、D、E，action为SUSPEND
如果是B,action为NEXT_NODE，next_node为N6节点的名称
如果是C,action为NEXT_NODE，next_node为N14节点的名称


### N6: 候选人的回复是否满足设定的要求
场景名: reply_match_question_requirement
模板变量：HR（AI）设定当前正在沟通的问题、历史对话
执行逻辑：CLG1
节点返回结果：
模型响应结果是”YES“，action为NEXT_NODE，next_node为N14节点的名称
否则action为SUSPEND

### N7: 候选人针对问题的沟通意愿
前置条件：Stage2并且当前询问问题不是判卷问题
场景名：candidate_communication_willingness_for_question
模板变量：历史对话
执行逻辑：CLG1
节点返回结果：
模型响应结果是”YES“，action为NEXT_NODE，next_node为N14节点的名称
否则action为SUSPEND

### N8: 候选人对职位是否有意向
前置条件：Stage3
场景名：candidate_position_willingness
模板变量：历史对话
执行逻辑：CLG1

### N9: 基于知识库回复求职者
场景名: answer_based_on_knowledge
模板变量：职位信息、知识库信息、历史对话、候选人最后一条消息
执行逻辑：额外查询职位对应的知识库信息，和入参中上下文中已存在的其他模板变量，继续执行CLG1
节点返回结果：
模型响应结果是”not_found“，action为NEXT_NODE，next_node为N10节点的名称
否则action为SEND_MESSAGE，message为模型响应的消息


### N10：无知识库时兜底回复
场景名: answer_without_knowledge
模板变量：历史对话、候选人最后一条消息
执行逻辑：CLG1
节点返回结果：
action为SEND_MESSAGE，message为模型响应的消息

### N11: 陪候选人闲聊
场景名：casual_conversation
模板变量：历史对话、职位信息、HR（AI）最后一句话
执行逻辑：CLG1
节点返回结果：
action为SEND_MESSAGE，message为模型响应的消息

### N12：高情商回复（结束语）
场景名: high_eq_response
模板变量：历史对话、职位信息、HR（AI）最后一句话、招聘方设置的当前职位的问题列表
执行逻辑：CLG1
节点返回结果：
action为SEND_MESSAGE，message为模型响应的消息

### N13：复聊语
场景名: resume_conversation
模板变量：职位名称、历史对话
执行逻辑：CLG1
节点返回结果：
action为SEND_MESSAGE，message为模型响应的消息

### N14：HR询问的问题处理（无需执行大模型）
场景名: information_gathering_question
模板变量：无需执行大模型
执行逻辑：
step1.如果当前会话处于Stage1，查询职位设定的要询问的问题，如果没有设定问题，更新会话阶段为Stage3对应的状态值；如果有问题，则初始化职位问题到当前会话问题中，同时设定会话阶段为Stage2对应的状态值，并执行step3
step2.如果当前会话处于Stage2，查询当前会话正在询问的问题，更新状态为完成
step3.查询会话下一个要询问的问题，如果没有，更新会话阶段为state3对应的状态值，返回：action为None
有下一个要询问的问题，更新会话问题状态为沟通中，返回：action为SEND_MESSAGE，message为要询问的问题

### N15: 问题询问阶段处理（复合节点，无需执行大模型）
前置条件：Stage1且职位存在有效的设定问题，或者Stage2
场景名：information_gathering
模板变量：无需执行大模型
执行逻辑：
1.如果是Stage1，且职位未设定有效的问题，action:None，否则：action:NEXT_NODE,next_node:N14
2.如果是Stage2，如果当前职位属于判卷问题，action:NEXT_NODE,next_node:N5；否则：action:NEXT_NODE,next_node:N7
3.如果是其他Stage，action:None




# 通用执行逻辑
执行逻辑是指节点中的具体代码逻辑
## CLG1
1.根据场景名从prompt_config中读取对应的配置
2.根据prompt配置从对应的prompt模板文件中读取prompt模板
3.替换prompt模板中的变量
5.根据对应的配置调用大模型进行执行
备注：可以封装为通用函数，执行类型java中StringSubstitutorParam；StringSubstitutorUtils.replace(promptMasterConfigBO.getPromptTemplate(), promptParams);

# 会话状态
## 会话状态
State1: 会话开启
State2: 沟通中
State3: 中断
State4: 会话结束

## 会话流程执行阶段
Stage1：开场白阶段（HR主动打招呼，或者候选人主动打招呼）
Stage2：问题询问阶段（HR（AI）正在就一下问题询问候选人）
Stage3：职位意向询问阶段
Stage4：撮合完成



# 业务执行流程
会话开启：
当HR（AI）主动联系候选人时，触发HR(AI)会话的创建及会话消息的保存；
当候选人投递或主动联系HR时，触发HR(AI)会话的创建，如果是有消息，同时触发会话消息的保存；

过程沟通：
触发时机：接收到候选人的消息
先保存候选人的消息到HR和候选人的消息表
执行流程：
基于流程节点的串行状态转移和执行，耗时过长，为了提高响应时间，对细分的节点组合成多个大节点，同时并行操作，提高响应效率，具体如下：
CombineNode1:前置过滤判断，组合N1、N2

CombineNode2: 问题阶段处理逻辑，等同于N15节点，组合N5、N6、N7、N14
CombineNode3: 消息回复方法，组合N3、N4、N9、N10、N11

你是一个研发专家，请你基于节点的定义和流转逻辑，完善业务执行流程的方案设计，主要是节点组合及并行，提高响应时间，有问题可以询问我，和我进行充分的方案沟通







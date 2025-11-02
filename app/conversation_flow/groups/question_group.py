"""
问题阶段处理组执行器

组合节点：问题路由 -> 相关性检查/满足度检查/沟通意愿检查 -> 问题处理
条件路由：根据问题类型（判卷/非判卷）选择不同路径
"""
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.question_stage import (
    QuestionRouterNode,
    RelevanceCheckNode,
    RequirementMatchNode,
    QuestionWillingnessNode,
    QuestionHandlerNode,
)

logger = structlog.get_logger(__name__)


class QuestionGroupExecutor:
    """问题阶段处理组执行器（N15->N5/N6/N7->N14）"""

    def __init__(self, db: AsyncSession):
        """
        初始化问题组执行器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.question_router_node = QuestionRouterNode(db)
        self.relevance_check_node = RelevanceCheckNode()
        self.requirement_match_node = RequirementMatchNode()
        self.question_willingness_node = QuestionWillingnessNode()
        self.question_handler_node = QuestionHandlerNode(db)

        logger.info("question_group_executor_initialized")

    async def execute(self, context: ConversationContext) -> NodeResult:
        """
        执行问题处理链

        执行流程：
        1. 问题路由判断（Stage1初始化 或 Stage2判断问题类型）
        2. 根据路由结果执行对应路径：
           - 判卷问题：相关性检查 -> 满足度检查 -> 问题处理
           - 非判卷问题：沟通意愿检查 -> 问题处理
           - Stage1初始化：问题处理
        3. 返回最终结果

        Args:
            context: 会话上下文

        Returns:
            节点执行结果
        """
        logger.debug(
            "question_group_execution_started",
            stage=context.conversation_stage.value
        )

        # ========== Step1: 执行问题路由判断 ==========
        question_router_result = await self.question_router_node.execute(context)

        # 问题路由返回NONE，说明不需要问题处理
        if question_router_result.action == NodeAction.NONE:
            logger.info("question_router_returned_none_skip_question_processing")
            return question_router_result

        # ========== Step2: 根据路由结果执行对应路径 ==========

        # 路由到问题处理（Stage1初始化场景）
        if "information_gathering_question" in question_router_result.next_node:
            logger.info("question_router_route_to_question_handler_init_questions")
            return await self.question_handler_node.execute(context)

        # 路由到相关性检查（判卷问题）
        elif "relevance_reply_and_question" in question_router_result.next_node:
            logger.info("question_router_route_to_relevance_check_scoring_question")

            # 执行相关性检查：相关性检查
            relevance_check_result = await self.relevance_check_node.execute(context)

            # 相关性检查返回SUSPEND，直接返回
            if relevance_check_result.action == NodeAction.SUSPEND:
                logger.warning("relevance_check_suspended", reason=relevance_check_result.reason)
                return relevance_check_result

            # 相关性检查路由到问题处理（答非所问，C）
            if "information_gathering_question" in relevance_check_result.next_node:
                logger.info("relevance_check_route_to_question_handler_irrelevant_answer")
                return await self.question_handler_node.execute(context)

            # 相关性检查路由到满足度检查（相关且有效，B）
            if "reply_match_question_requirement" in relevance_check_result.next_node:
                logger.info("relevance_check_route_to_requirement_match_check_requirement")

                # 执行满足度检查：满足度检查
                requirement_match_result = await self.requirement_match_node.execute(context)

                # 满足度检查返回SUSPEND，直接返回
                if requirement_match_result.action == NodeAction.SUSPEND:
                    logger.warning("requirement_match_suspended", reason=requirement_match_result.reason)
                    return requirement_match_result

                # 满足度检查路由到问题处理（满足要求）
                if "information_gathering_question" in requirement_match_result.next_node:
                    logger.info("requirement_match_route_to_question_handler_requirement_satisfied")
                    return await self.question_handler_node.execute(context)

        # 路由到沟通意愿检查（非判卷问题）
        elif "candidate_communication_willingness_for_question" in question_router_result.next_node:
            logger.info("question_router_route_to_question_willingness_non_scoring_question")

            # 执行沟通意愿检查：沟通意愿检查
            question_willingness_result = await self.question_willingness_node.execute(context)

            # 沟通意愿检查返回SUSPEND，直接返回
            if question_willingness_result.action == NodeAction.SUSPEND:
                logger.warning("question_willingness_suspended", reason=question_willingness_result.reason)
                return question_willingness_result

            # 沟通意愿检查路由到问题处理（愿意沟通）
            if "information_gathering_question" in question_willingness_result.next_node:
                logger.info("question_willingness_route_to_question_handler_willing_to_communicate")
                return await self.question_handler_node.execute(context)

        # ========== Step3: 未匹配到路由，返回错误 ==========
        logger.error(
            "question_group_unexpected_route",
            next_node=question_router_result.next_node
        )

        return NodeResult(
            node_name="QuestionGroup",
            action=NodeAction.NONE,
            reason=f"未知的路由路径: {question_router_result.next_node}"
        )

"""
问题阶段处理组执行器

组合节点：N15 -> N5/N6/N7 -> N14
条件路由：根据问题类型（判卷/非判卷）选择不同路径
"""
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.question_stage import (
    N15QuestionRouterNode,
    N5RelevanceCheckNode,
    N6RequirementMatchNode,
    N7QuestionWillingnessNode,
    N14QuestionHandlerNode,
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
        self.n15 = N15QuestionRouterNode(db)
        self.n5 = N5RelevanceCheckNode()
        self.n6 = N6RequirementMatchNode()
        self.n7 = N7QuestionWillingnessNode()
        self.n14 = N14QuestionHandlerNode(db)

        logger.info("question_group_executor_initialized")

    async def execute(self, context: ConversationContext) -> NodeResult:
        """
        执行问题处理链

        执行流程：
        1. N15路由判断（Stage1初始化 或 Stage2判断问题类型）
        2. 根据路由结果执行对应路径：
           - 判卷问题：N5 -> N6 -> N14
           - 非判卷问题：N7 -> N14
           - Stage1初始化：N14
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

        # ========== Step1: 执行N15路由判断 ==========
        n15_result = await self.n15.execute(context)

        # N15返回NONE，说明不需要问题处理
        if n15_result.action == NodeAction.NONE:
            logger.info("n15_returned_none_skip_question_processing")
            return n15_result

        # ========== Step2: 根据路由结果执行对应路径 ==========

        # 路由到N14（Stage1初始化场景）
        if "N14" in n15_result.next_node:
            logger.info("n15_route_to_n14_init_questions")
            return await self.n14.execute(context)

        # 路由到N5（判卷问题）
        elif "N5" in n15_result.next_node:
            logger.info("n15_route_to_n5_scoring_question")

            # 执行N5：相关性检查
            n5_result = await self.n5.execute(context)

            # N5返回SUSPEND，直接返回
            if n5_result.action == NodeAction.SUSPEND:
                logger.warning("n5_suspended", reason=n5_result.reason)
                return n5_result

            # N5路由到N14（答非所问，C）
            if "N14" in n5_result.next_node:
                logger.info("n5_route_to_n14_irrelevant_answer")
                return await self.n14.execute(context)

            # N5路由到N6（相关且有效，B）
            if "N6" in n5_result.next_node:
                logger.info("n5_route_to_n6_check_requirement")

                # 执行N6：满足度检查
                n6_result = await self.n6.execute(context)

                # N6返回SUSPEND，直接返回
                if n6_result.action == NodeAction.SUSPEND:
                    logger.warning("n6_suspended", reason=n6_result.reason)
                    return n6_result

                # N6路由到N14（满足要求）
                if "N14" in n6_result.next_node:
                    logger.info("n6_route_to_n14_requirement_satisfied")
                    return await self.n14.execute(context)

        # 路由到N7（非判卷问题）
        elif "N7" in n15_result.next_node:
            logger.info("n15_route_to_n7_non_scoring_question")

            # 执行N7：沟通意愿检查
            n7_result = await self.n7.execute(context)

            # N7返回SUSPEND，直接返回
            if n7_result.action == NodeAction.SUSPEND:
                logger.warning("n7_suspended", reason=n7_result.reason)
                return n7_result

            # N7路由到N14（愿意沟通）
            if "N14" in n7_result.next_node:
                logger.info("n7_route_to_n14_willing_to_communicate")
                return await self.n14.execute(context)

        # ========== Step3: 未匹配到路由，返回错误 ==========
        logger.error(
            "question_group_unexpected_route",
            next_node=n15_result.next_node
        )

        return NodeResult(
            node_name="QuestionGroup",
            action=NodeAction.NONE,
            reason=f"未知的路由路径: {n15_result.next_node}"
        )

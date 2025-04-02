import pickle
import pandas as pd
from pathlib import Path
from typing import cast, Optional, Dict, Any
from langchain_graphrag.indexing import TextUnitExtractor, IndexerArtifacts
from langchain_openai import ChatOpenAI
from langchain_community.cache import SQLiteCache
from langchain_openai import OpenAIEmbeddings
from langchain_chroma.vectorstores import Chroma as ChromaVectorStore
from langchain_graphrag.query.global_search import GlobalSearch
from langchain_graphrag.query.global_search.community_weight_calculator import CommunityWeightCalculator
from langchain_graphrag.query.global_search.key_points_aggregator import (
    KeyPointsAggregator, KeyPointsAggregatorPromptBuilder, KeyPointsContextBuilder
)
from langchain_graphrag.query.global_search.key_points_generator import (
    CommunityReportContextBuilder, KeyPointsGenerator, KeyPointsGeneratorPromptBuilder
)
from langchain_graphrag.query.local_search import (
    LocalSearch, LocalSearchPromptBuilder, LocalSearchRetriever
)
from langchain_graphrag.query.local_search.context_builders import ContextBuilder
from langchain_graphrag.query.local_search.context_selectors import ContextSelector
from langchain_graphrag.types.graphs.community import CommunityLevel
from langchain_graphrag.utils import TiktokenCounter

import warnings
warnings.filterwarnings("ignore")

class GraphRAG:
    def __init__(
        self,
        artifacts_path: str,
        llm_config: Dict[str, Any],
        community_level: int = 0
    ):
        """
        初始化GraphRAG系统
        
        参数:
            artifacts_path: 知识图谱数据路径
            llm_config: LLM配置字典
                {
                    "model": "deepseek-chat",
                    "base_url": "http://139.224.116.116:3000/v1",
                    "api_key": "sk-..."
                }
            community_level: 社区级别阈值
        """
        self.artifacts_path = Path(artifacts_path)
        self.llm_config = llm_config
        self.community_level = community_level
        self.artifacts = None
        self.global_search = None
        self.local_search = None
        self.llm = None
        
        self._initialize()
    
    def _initialize(self):
        """初始化系统组件"""
        # 1. 加载知识图谱数据
        self.artifacts = self._load_artifacts(self.artifacts_path)
        
        # 2. 初始化LLM
        self.llm = ChatOpenAI(
            model=self.llm_config["model"],
            base_url=self.llm_config["base_url"],
            api_key=self.llm_config["api_key"]
        )
        
        # 3. 初始化全局搜索
        self._init_global_search()
        
        # 4. 初始化本地搜索（可选）
        # self._init_local_search()
    
    def _load_artifacts(self, path: Path) -> IndexerArtifacts:
        """加载知识图谱数据"""
        entities = pd.read_parquet(path / "entities.parquet")
        relationships = pd.read_parquet(path / "relationships.parquet")
        text_units = pd.read_parquet(path / "text_units.parquet")
        communities_reports = pd.read_parquet(path / "communities_reports.parquet")

        # 加载pickle文件
        def load_pickle(file_path):
            if file_path.exists():
                with file_path.open("rb") as fp:
                    return pickle.load(fp)
            return None

        merged_graph = load_pickle(path / "merged-graph.pickle")
        summarized_graph = load_pickle(path / "summarized-graph.pickle")
        communities = load_pickle(path / "community_info.pickle")

        return IndexerArtifacts(
            entities=entities,
            relationships=relationships,
            text_units=text_units,
            communities_reports=communities_reports,
            merged_graph=merged_graph,
            summarized_graph=summarized_graph,
            communities=communities,
        )
    
    def _init_global_search(self):
        """初始化全局搜索组件"""
        # 社区报告上下文构建器
        report_context_builder = CommunityReportContextBuilder(
            community_level=cast(CommunityLevel, self.community_level),
            weight_calculator=CommunityWeightCalculator(),
            artifacts=self.artifacts,
            token_counter=TiktokenCounter(),
        )
        
        # 关键点生成器
        kp_generator = KeyPointsGenerator(
            llm=self.llm,
            prompt_builder=KeyPointsGeneratorPromptBuilder(
                show_references=False,
                repeat_instructions=True
            ),
            context_builder=report_context_builder,
        )
        
        # 关键点聚合器
        kp_aggregator = KeyPointsAggregator(
            llm=self.llm,
            prompt_builder=KeyPointsAggregatorPromptBuilder(
                show_references=False,
                repeat_instructions=True,
            ),
            context_builder=KeyPointsContextBuilder(
                token_counter=TiktokenCounter(),
            ),
            output_raw=True,
        )
        
        # 全局搜索实例
        self.global_search = GlobalSearch(
            kp_generator=kp_generator,
            kp_aggregator=kp_aggregator,
            generation_chain_config={"tags": ["kp-generation"]},
            aggregation_chain_config={"tags": ["kp-aggregation"]},
        )
    
    def query(self, question: str) -> str:
        """
        执行查询
        
        参数:
            question: 用户提问
            
        返回:
            回答结果
        """
        if not self.global_search:
            raise ValueError("Global search not initialized")
        
        return self.global_search.invoke(question)
    


# 使用示例
if __name__ == "__main__":
    # 配置参数
    config = {
        "artifacts_path": "F:\\bigmodel\\meet-Pok-mon\\4.KGqa\\Pokemon-KGQA\\RAG\\artifacts",
        "llm_config": {
            "model": "deepseek-chat",
            "base_url": "http://139.224.116.116:3000/v1",
            "api_key": "sk-36oMlDApF5Nlg0v23014A4B69e864000944151Cd75D82076"
        },
        "community_level": 0
    }
    
    # 初始化GraphRAG系统
    graph_rag = GraphRAG(
        artifacts_path=config["artifacts_path"],
        llm_config=config["llm_config"],
        community_level=config["community_level"]
    )
    
    # 执行查询
    question = "介绍一下恭平是谁？"
    response = graph_rag.query(question)
    print(response.content)
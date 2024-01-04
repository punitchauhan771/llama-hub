"""RAGatouille Retriever Pack."""


from typing import Any, Dict, List, Optional

from llama_index.schema import Document, NodeWithScore

from llama_index.llama_pack.base import BaseLlamaPack
from llama_index.llms import Replicate, OpenAI
from llama_index.llms.llm import LLM
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.retrievers import BaseRetriever
from llama_index.service_context import ServiceContext
from llama_index.indices.query.schema import QueryBundle


class CustomRetriever(BaseRetriever):
    """Custom retriever."""
    
    def __init__(self, rag_obj: Any, index_name: str, **kwargs: Any) -> None:
        """Init params."""
        try:
            import ragatouille
        except ImportError:
            raise ValueError("RAGatouille is not installed. Please install it with `pip install ragatouille`.")
        self.rag_obj = rag_obj
        self.index_name = index_name

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve."""
        return self.rag_obj.search(query_bundle.query_str, index_name=self.index_name)


class RAGatouilleRetrieverPack(BaseLlamaPack):
    """RAGatouille Retriever pack."""

    def __init__(
        self,
        documents: List[Document],
        model_name: str = "colbert-ir/colbertv2.0",
        index_name: str = "my_index",
        llm: Optional[LLM] = None,
        index_path: Optional[str] = None,
    ) -> None:
        """Init params."""
        self._model_name = model_name
        try:
            import ragatouille
            from ragatouille import RAGPretrainedModel
        except ImportError:
            raise ValueError("RAGatouille is not installed. Please install it with `pip install ragatouille`.")


        doc_txts = [doc.get_content() for doc in documents]

        # index the documents
        if index_path is None:
            RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
            index_path = RAG.index(index_name=index_name, collection=doc_txts)
        else:
            RAG = RAGPretrainedModel.from_index(index_path)

        self.custom_retriever = CustomRetriever(RAG, index_name=index_name)

        self.RAG = RAG
        self.documents = documents

        self.llm = llm or OpenAI(model="gpt-3.5-turbo")
        self.query_engine = RetrieverQueryEngine.from_args(
            self.custom_retriever,
            service_context=ServiceContext.from_defaults(llm=llm)
        )

    def get_modules(self) -> Dict[str, Any]:
        """Get modules."""
        return {
            "RAG": self.RAG,
            "documents": self.documents,
            "retriever": self.custom_retriever,
            "llm": self.llm,
            "query_engine": self.query_engine,
        }

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the pipeline."""
        return self.query_engine.query(*args, **kwargs)

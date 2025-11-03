#!/usr/bin/env python
# -*- coding: utf-8 -*-

from langchain_openai import OpenAIEmbeddings
from .vectordb_loader import VectorDBLoader

class RagRetrieve:
    def __init__(self, logger, asset_info={}):
        self._logger = logger
        self._vector_db_loader = None
        self._vector_db = None
        self._set_asset(**asset_info)

    def _set_asset(self, knowledge_id, embedding_server_path, embed_model_nm, vectordb_type, vectordb_path, api_key=None):
        self._knowledge_id = knowledge_id
        self._embedding_server_path = embedding_server_path
        self._embed_model_nm = embed_model_nm
        self._vectordb_type = vectordb_type
        self._vectordb_path = vectordb_path
        self._api_key = api_key

    async def retrieve(self, query, top_k, check_embedding_ctx_length=False, threshold=0.1):
        # collection_name: as vectorDB's table == knowledge name
        # check_embedding_ctx_length: ??

        embedding_model = OpenAIEmbeddings(openai_api_base=self._embedding_server_path, model=self._embed_model_nm, api_key=self._api_key, check_embedding_ctx_length=check_embedding_ctx_length)
        if not self._vector_db:
            vector_db_loader = VectorDBLoader(self._logger)
            self._vector_db = vector_db_loader.load(
                db_type=self._vectordb_type,
                connection_string=self._vectordb_path,
                collection_name=self._knowledge_id,
                embedding_model=embedding_model
            )

        documents = await self._vector_db.search(query=query, top_k=top_k, score_threshold=threshold)
        retrieved_documents = [doc["text"] for doc in documents]
        document_sources = [doc["metadata"] for doc in documents]

        if not retrieved_documents:
            retrieved_documents = ['- 216 -\n【용어풀이】이 특별약관에서 ‘해당 보험료’라 함은 대인배상Ⅰ･Ⅱ, 대물배상, 대물배상 가입금액 확장 특별약관, 자기신체사고, 자동차상해 특별약관, 무보험자동차에 의한 상해, 자기차량손해(차대차 충돌 및 도난), 자기차량손해 포괄담보 특별약관의 보험료를 말합니다.', '- 69 -\n면에 기재하여 드립니다.1. 보험계약자. 다만, 보험계약자가 이 보험계약의 권리･의무를 피보험자동차의 양수인에게 이전함에 따라 보험계약자가 변경되는 경우에는 제48조(피보험자동차의 양도)에 따릅니다.2. 보험가입금액, 특별약관 등 그 밖의 계약의 내용② 보험회사는 제1항에 따라 계약내용의 변경으로 보험료가 변경된 경우 보험계약자에게 보험료를 반환하거나 추가보험료를 청구할 수 있습니다. ③ 보험계약 체결 후 보험계약자가 사망한 경우 이 보험계약에 의한 보험계약자의 권리･의무는 사망시점에서의 법정상속인에게 이전합니다.\n【용어풀이】‘법정상속인’이란 피상속인의 사망에 의하여 민법의 규정에 의한 상속순위에 따라 상속받는 자를 말합니다.', '및 해지)’에 해당하는 경우 해당 사실을 보험계약자에게 통보한 후, 보험계약자가 고지한 은행 계좌 또는 신용카드에서 할인한 보험료를 지체 없이 정산합니다.제4조(특별약관의 무효 및 해지)① 회사가 확인한 점수가 기명피보험자 본인의 점수가 아닌 경우 이 특별약관은 무효가 됩니다. 이 경우 보험계약자(또는 피보험자)는 이 특별약관에 의해 할인받은 보험료를 회사에 반환하여야 합니다.② 보험증권에 기재되어 있는 보험기간 동안에 계약변경으로 인하여 이 특별약관', '특별약관 계약의 임의해지)① 보험계약자는 언제든지 이 특별약관 계약을 해지할 수 있으며, 이 경우 보험계약은 보험의 책임개시일을 기준으로 연간보험료 전액을 납입하는 계약으로 전환됩니다.    ② 위 제①항에 따라 이 특별약관 계약이 임의해지된 경우 보험계약자 또는 피보험자는 보험의 책임개시일을 기준으로 연간보험료 전액과 회사에 이미 납입한 보험료의 차이에 해당하는 금액을 지체없이 납입하여야 합니다. 제6조(준용규정)이 특별약관에 정하지 않은 사항은 보통약관에 따릅니다.제22장 커넥트데이 분할납입 추가 특별약관제1조(적용대상)이 추가 특별약관은 커넥트데이 특별약관에 가입하고, 보험기간에 해당하는 보험 - 242 -', '③ 타인을 위한 보험계약에서 보험계약자는 기명피보험자의 동의를 얻거나 보험증권을 소지한 경우에 한하여 제1항 또는 제2항의 규정에 따라 보험계약을 해지하거나 또는 해제할 수 있습니다.', '【용어풀이】기명피보험자의 지명1인보험계약의 체결시에 기명피보험자가 지명하는 보험증권상의 1인단, 기명피보험자 및 그의 배우자는 제외\n제3조(준용규정) 이 특별약관에서 정하지 않은 사항은 보통약관에 따릅니다.제4조(기타)', '제3조(보험료 할인) 보험회사는 이 특별약관 가입기간 동안의 해당 보험료에 대하여 별도로 정한 할인율을 적용하여 할인하여 드립니다.\n【용어풀이】이 특별약관에서 ‘해당 보험료’라 함은 대인배상Ⅰ･Ⅱ, 대물배상, 대물배상 가입금액 확장 특별약관, 자기신체사고, 자동차상해 특별약관, 무보험자동차에 의한 상해, 자기차량손해(차대차 충돌 및 도난), 자기차량손해 포괄담보 특별약관의 보험료를 말합니다.', '⋇ 同  Guide Book은 보험약관의 개념 및 구성 등을 간략하게 소개하고, 소비자 입장에서 약관 주요내용 등을 쉽게 찾고 이해할 수 있는 방법을 안내하는 것을 목적으로 함         1. 보험약관이란?보험약관은 가입하신 보험계약의 내용 및 조건 등을 미리 정하여 놓은 계약조항으로 보험계약자와 보험회사의 권리 및 의무를 규정하고 있습니다. 특히, 청약철회, 계약취소, 보험금 지급 및 지급제한 사항 등 약관의 중요사항에 대한 설명이 들어 있으니 반드시 확인하셔야 합니다.  2. 한 눈에 보는 약관의 구성약관 이용 가이드북약관을 쉽게 잘 이용할 수 있도록 약관의 구성, 쉽게 찾는 방법 등의 내용을 담고 있는 지침서시각화된 약관 요약서약관을 쉽게 이해할 수 있도록 계약 주요내용 및 유의사항 등을', '경우: 이미 경과한 기간에 대하여 단기요율로 계산한 보험료를 뺀 잔액3. 보험계약이 해지(제52조의2에 따른 위법계약 해지를 포함한다)된 경우, 계약을 해지하기 전에 보험회사가 보상하여야 하는 사고가 발생한 때에는 보험료를 환급하지 않습니다.④ 제3항에서 ‘보험계약자 또는 피보험자에게 책임이 있는 사유’라 함은 다음의 경우를 말합니다.1. 보험계약자 또는 피보험자가 임의 해지하는 경우(의무보험의 해지는 제외)', '③ 보험료 납입관련 특별약관◦ 보험료 분할납입 특별약관 : 보험계약자가 납입할 1년간의 보험료를 보험증권에 기재된 회수 및 금액으로 분할하여 납입할 수 있도록 하는 특별약관입니다.◦ 보험료 자동이체납입 및 자동갱신 특별약관 : 보험계약자가 보험료를 보험계약자 또는 기명피보험자의 지정은행 계좌를 통하여 자동이체납입하기로 하고, 이 보험계약기간 만료일을 보험기간 시기로 하여 갱신계약을 체결할 것을 약정하는 경우에 적용하는 특별약관입니다.④ 기타 ◦ 의무보험 일시담보 특별약관 : 양수인이 양도일 이후 15일 이내에 자동차보험에 가입하지 않고 사고를 야기한 경우 대인Ⅰ의 보상기준에 따라 손해배상을 하는 특별약관입니다.◦ 다른 자동차 운전담보 특별약관 : 기명피보험자 또는 기명피보험자의 배우자가 다른 자동차를 운전중 대인, 대물, 자기신체사고를 일으켰을 때 피보험자가 운전한 다른 자동차의 보험계약으로 보상될 수 있는 금액을 초과하는 경우에 한하여 그 초과액을 보상합니다.기명피보험자가']
        return retrieved_documents, document_sources
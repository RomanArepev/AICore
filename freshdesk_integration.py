import os
import requests
import base64
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class FreshDeskConfig(BaseModel):
    domain: str
    api_key: str

class FreshDeskIntegration:
    def __init__(self, llm: ChatOpenAI = None):
        # Create Base64 encoded API key from username and password
        user = ""
        password = ""
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        
        self.config = FreshDeskConfig(
            domain=os.getenv("FRESHDESK_DOMAIN", "itsgroup.freshdesk.com"),
            api_key=credentials
        )
        self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.01)

    async def get_tickets(self, query_text: str):
        """Get tickets from FreshDesk based on search query"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self.config.api_key}'
        }
        
        url = f"https://{self.config.domain}/api/v2/search/tickets"
        params = {
            'query': f'"{query_text}"'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"FreshDesk API error: {str(e)}")
            return None

    async def analyze_with_gpt(self, tickets_data: dict, original_query: str, first_gpt_response: str):
        """Analyze tickets using GPT"""
        if not tickets_data:
            return first_gpt_response
        
        tickets_context = "\n".join([
            f"Ticket #{ticket.get('id')}: {ticket.get('subject')} - {ticket.get('description')}"
            for ticket in tickets_data.get('results', [])[:5]
        ])
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a ticket information system. Your task is to:
            1. Look through the tickets and find EXACT matches for the query keywords
            2. Return ONLY the exact information from matching tickets
            3. Do not add any suggestions, speculations, or requests for more information
            4. If multiple tickets match different parts of the query, list them separately
            
            Format your response as:
            "Found in Ticket #X: [exact ticket information]"
            
            Available tickets:
            {context}"""),
            ("human", "{input}")
        ])
        
        analysis_context = {
            "original_query": original_query,
            "tickets": tickets_context
        }
        
        try:
            final_response = self.llm.invoke(
                analysis_prompt.format(
                    context=str(analysis_context),
                    input=f"List exact matches for: {original_query}"
                )
            )
            return str(final_response.content) if hasattr(final_response, 'content') else str(final_response)
        except Exception as e:
            return f"Error processing response: {str(e)}"

    async def process_query(self, query_text: str, initial_response: str):
        """Process query using FreshDesk"""
        # Test data instead of real FreshDesk API call
        freshdesk_data = await self.get_tickets(query_text)
        
        # Analyze all data together using GPT
        final_answer = await self.analyze_with_gpt(
            freshdesk_data,
            query_text,
            initial_response
        )
        
        return {
            "answer": final_answer,
            "freshdesk_tickets_found": bool(freshdesk_data and freshdesk_data.get('results'))
        } 
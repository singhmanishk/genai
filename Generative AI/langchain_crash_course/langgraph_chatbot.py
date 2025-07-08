import streamlit as st
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import json
import time

# Define the state and node types
class NodeType(Enum):
    ROUTER = "router"
    FAQ_GENERAL = "faq_general"
    FAQ_SPECIFIC = "faq_specific"
    PAYMENT = "payment"
    ORDERS = "orders"
    FAQ_ROUTER = "faq_router"

@dataclass
class ChatState:
    messages: List[Dict[str, str]]
    current_node: NodeType
    context: Dict[str, Any]
    user_input: str
    response: str

class LangGraphChatbot:
    def __init__(self):
        self.state = ChatState(
            messages=[],
            current_node=NodeType.ROUTER,
            context={},
            user_input="",
            response=""
        )
        
        # Sample data for different nodes
        self.faq_general_data = {
            "what are your hours": "We are open 24/7 for online support. Our phone support is available Monday-Friday 9AM-6PM EST.",
            "how to contact support": "You can reach us via email at support@company.com, phone at 1-800-SUPPORT, or through this chat.",
            "where are you located": "Our headquarters is in New York, but we serve customers worldwide.",
            "what services do you offer": "We offer e-commerce solutions, customer support, payment processing, and order management."
        }
        
        self.faq_specific_data = {
            "how to return an item": "To return an item, go to 'My Orders', select the item, and click 'Return'. You have 30 days from purchase.",
            "shipping policy": "We offer free shipping on orders over $50. Standard shipping takes 3-5 business days.",
            "warranty information": "All products come with a 1-year manufacturer warranty. Extended warranties are available for purchase.",
            "product specifications": "Product specifications vary by item. Check the product page for detailed technical specifications."
        }
        
        self.payment_data = {
            "payment methods": "We accept all major credit cards, PayPal, Apple Pay, and Google Pay.",
            "payment failed": "If your payment failed, please check your card details and try again. Contact your bank if issues persist.",
            "refund process": "Refunds are processed within 5-7 business days to your original payment method.",
            "payment security": "We use SSL encryption and PCI compliance to ensure your payment information is secure."
        }
        
        self.orders_data = {
            "track order": "To track your order, go to 'My Orders' and click on the tracking number, or use our order tracking page.",
            "cancel order": "Orders can be cancelled within 1 hour of placement. After that, you'll need to return the item.",
            "order status": "You can check your order status in 'My Orders' section of your account.",
            "delivery time": "Standard delivery is 3-5 business days. Express delivery is 1-2 business days."
        }

    def classify_intent(self, user_input: str) -> NodeType:
        """Classify user intent to route to appropriate node"""
        user_input_lower = user_input.lower()
        
        # FAQ keywords
        faq_keywords = ["help", "question", "how", "what", "when", "where", "why", "faq"]
        # Payment keywords
        payment_keywords = ["payment", "pay", "card", "billing", "charge", "refund", "money"]
        # Order keywords
        order_keywords = ["order", "track", "delivery", "shipping", "cancel", "status"]
        
        if any(keyword in user_input_lower for keyword in payment_keywords):
            return NodeType.PAYMENT
        elif any(keyword in user_input_lower for keyword in order_keywords):
            return NodeType.ORDERS
        elif any(keyword in user_input_lower for keyword in faq_keywords):
            return NodeType.FAQ_ROUTER
        else:
            return NodeType.FAQ_ROUTER  # Default to FAQ for general queries

    def classify_faq_type(self, user_input: str) -> NodeType:
        """Classify FAQ into general or specific"""
        user_input_lower = user_input.lower()
        
        # Specific FAQ keywords
        specific_keywords = ["return", "warranty", "shipping", "specifications", "technical"]
        
        if any(keyword in user_input_lower for keyword in specific_keywords):
            return NodeType.FAQ_SPECIFIC
        else:
            return NodeType.FAQ_GENERAL

    def find_best_match(self, user_input: str, data_dict: Dict[str, str]) -> str:
        """Find the best matching response from the data dictionary"""
        user_input_lower = user_input.lower()
        best_match = None
        highest_score = 0
        
        for key, value in data_dict.items():
            # Simple keyword matching
            keywords = key.split()
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            
            if score > highest_score:
                highest_score = score
                best_match = value
        
        return best_match if best_match else "I'm sorry, I don't have specific information about that. Could you please rephrase your question?"

    def router_node(self, state: ChatState) -> ChatState:
        """Main router node that directs to appropriate specialized nodes"""
        intent = self.classify_intent(state.user_input)
        state.current_node = intent
        
        if intent == NodeType.FAQ_ROUTER:
            return self.faq_router_node(state)
        elif intent == NodeType.PAYMENT:
            return self.payment_node(state)
        elif intent == NodeType.ORDERS:
            return self.orders_node(state)
        
        return state

    def faq_router_node(self, state: ChatState) -> ChatState:
        """FAQ router that determines general vs specific FAQ"""
        faq_type = self.classify_faq_type(state.user_input)
        state.current_node = faq_type
        
        if faq_type == NodeType.FAQ_GENERAL:
            return self.faq_general_node(state)
        else:
            return self.faq_specific_node(state)

    def faq_general_node(self, state: ChatState) -> ChatState:
        """Handle general FAQ questions"""
        response = self.find_best_match(state.user_input, self.faq_general_data)
        state.response = f"📋 **General FAQ**: {response}"
        return state

    def faq_specific_node(self, state: ChatState) -> ChatState:
        """Handle specific FAQ questions"""
        response = self.find_best_match(state.user_input, self.faq_specific_data)
        state.response = f"🔍 **Specific FAQ**: {response}"
        return state

    def payment_node(self, state: ChatState) -> ChatState:
        """Handle payment-related queries"""
        response = self.find_best_match(state.user_input, self.payment_data)
        state.response = f"💳 **Payment Support**: {response}"
        return state

    def orders_node(self, state: ChatState) -> ChatState:
        """Handle order-related queries"""
        response = self.find_best_match(state.user_input, self.orders_data)
        state.response = f"📦 **Order Support**: {response}"
        return state

    def process_message(self, user_input: str) -> str:
        """Process user message through the graph"""
        self.state.user_input = user_input
        
        # Start with router node
        self.state = self.router_node(self.state)
        
        # Add to message history
        self.state.messages.append({
            "role": "user",
            "content": user_input,
            "node": self.state.current_node.value
        })
        self.state.messages.append({
            "role": "assistant",
            "content": self.state.response,
            "node": self.state.current_node.value
        })
        
        return self.state.response

def main():
    st.set_page_config(
        page_title="Multi-Agent LangGraph Chatbot",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Multi-Agent LangGraph Chatbot")
    st.markdown("---")
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = LangGraphChatbot()
    
    # Sidebar with information
    with st.sidebar:
        st.header("🔧 Chatbot Architecture")
        st.markdown("""
        **Node Structure:**
        - 🎯 **Router Node**: Main entry point
        - ❓ **FAQ Router**: Directs to FAQ sub-nodes
            - 📋 **General FAQ**: Basic information
            - 🔍 **Specific FAQ**: Detailed topics
        - 💳 **Payment Node**: Payment-related queries
        - 📦 **Orders Node**: Order management
        """)
        
        st.header("📊 Current Session")
        total_messages = len(st.session_state.chatbot.state.messages)
        st.metric("Total Messages", total_messages)
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chatbot = LangGraphChatbot()
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chatbot.state.messages):
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        st.caption(f"Handled by: {message['node']}")
        
        # User input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Display user message immediately
            st.chat_message("user").write(user_input)
            
            # Process message through LangGraph
            with st.spinner("Processing..."):
                response = st.session_state.chatbot.process_message(user_input)
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response)
                st.caption(f"Handled by: {st.session_state.chatbot.state.current_node.value}")
            
            st.rerun()
    
    with col2:
        st.header("🔍 Node Activity")
        
        # Show current node
        if st.session_state.chatbot.state.current_node:
            st.info(f"**Current Node**: {st.session_state.chatbot.state.current_node.value}")
        
        # Show node statistics
        if st.session_state.chatbot.state.messages:
            node_counts = {}
            for msg in st.session_state.chatbot.state.messages:
                if msg["role"] == "assistant":
                    node = msg["node"]
                    node_counts[node] = node_counts.get(node, 0) + 1
            
            st.subheader("Node Usage")
            for node, count in node_counts.items():
                st.metric(node.replace("_", " ").title(), count)
        
        # Sample queries
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "What are your hours?",
            "How to return an item?",
            "Payment methods accepted?",
            "Track my order",
            "Refund process",
            "Shipping policy"
        ]
        
        for query in sample_queries:
            if st.button(query, key=f"sample_{query}"):
                # Simulate user input
                response = st.session_state.chatbot.process_message(query)
                st.rerun()

if __name__ == "__main__":
    main()

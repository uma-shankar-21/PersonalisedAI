import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

# =================================================
# EMBEDDING MODEL
# =================================================
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2",
    token=os.getenv("HF_TOKEN"),
)


# =================================================
# SUPPORTED BANKING DOMAINS
# =================================================

DOMAIN_EXAMPLES = {
    "account_balance": [
        "What is my account balance?",
        "How much money do I have in my account?",
        "Show my savings account balance",
        "Show my current account balance",
        "How much money is available in my account?",
        "What is my bank balance?",
    ],

    "transactions": [
        "Show my transactions",
        "Show my transaction history",
        "What did I spend my money on?",
        "Show my debit transactions",
        "Show my credit transactions",
        "Show my failed transactions",
        "Show my pending transactions",
        "Show transactions from last month",
        "Show my food expenses",
        "Show transactions for a merchant",
        "Where did I spend money?",
    ],

    "loans": [
        "Show my loans",
        "How much loan do I have left?",
        "What is my outstanding loan amount?",
        "What is my monthly EMI?",
        "How many EMIs are remaining?",
        "How many loan installments are left?",
        "What is my loan interest rate?",
        "When is my next EMI due?",
    ],

    "loan_payment_history": [
        "Show my loan payment history",
        "Show my EMI payment history",
        "When did I make my loan payments?",
        "Show loan payments from January",
        "Show payments for my loan",
    ],

    "bank_information": [
        "What accounts does this bank provide?",
        "What loan products does this bank offer?",
        "Tell me about savings accounts",
        "Explain current accounts",
        "What services does this bank provide?",
        "What banking products are available?",
    ],

    "banking_support": [
        "Why did my transaction fail?",
        "Why is my payment pending?",
        "Why was my account charged?",
        "Why did my debit transaction fail?",
        "Why is my banking transaction not completed?",
    ],
}


# =================================================
# PRECOMPUTE DOMAIN EMBEDDINGS
# =================================================

DOMAIN_VECTORS = {}

for intent, examples in DOMAIN_EXAMPLES.items():

    DOMAIN_VECTORS[intent] = embedding_model.encode(
        examples
    )


# =================================================
# OTHER PERSON DATA DETECTION
# =================================================

def is_requesting_other_person_data(message):

    message = message.lower()

    patterns = [
        r"balance of .+",
        r"account of .+",
        r"transactions of .+",
        r"loan of .+",
        r"emi of .+",
        r"bank balance of .+",
        r"show .+'s balance",
        r"show .+'s transactions",
        r"show .+'s account",
    ]

    for pattern in patterns:

        if re.search(
            pattern,
            message,
        ):

            return True

    return False


# =================================================
# UNAUTHORIZED / MALICIOUS REQUEST DETECTION
# =================================================

def is_unauthorized_request(message):

    message = message.lower()

    suspicious_patterns = [
        "steal money",
        "steal balance",
        "steal bank",
        "hack someone",
        "hack another",
        "hack bank account",
        "access someone else's account",
        "access another person's account",
        "bypass bank security",
        "bypass banking security",
        "exploit bank loophole",
        "exploit banking loophole",
        "find a banking loophole",
    ]

    for pattern in suspicious_patterns:

        if pattern in message:

            return True

    return False


# =================================================
# SIMILARITY CLASSIFICATION
# =================================================

def get_similarity_result(message):

    query_vector = embedding_model.encode(
        [message]
    )

    best_intent = None
    best_score = 0.0

    for intent, vectors in DOMAIN_VECTORS.items():

        scores = cosine_similarity(
            query_vector,
            vectors,
        )[0]

        score = float(
            max(scores)
        )

        if score > best_score:

            best_score = score
            best_intent = intent

    return {
        "intent": best_intent,
        "score": best_score,
    }


# =================================================
# MAIN QUERY CLASSIFIER
# =================================================

def classify_query(message):

    # ---------------------------------------------
    # 1. OTHER PERSON'S PRIVATE BANKING DATA
    # ---------------------------------------------

    if is_requesting_other_person_data(
        message
    ):

        return {
            "category": "OTHER_PERSON_DATA",
            "intent": None,
            "score": None,
        }

    # ---------------------------------------------
    # 2. UNAUTHORIZED / MALICIOUS REQUEST
    # ---------------------------------------------

    if is_unauthorized_request(
        message
    ):

        return {
            "category": "UNAUTHORIZED_REQUEST",
            "intent": None,
            "score": None,
        }

    # ---------------------------------------------
    # 3. VECTOR SIMILARITY
    # ---------------------------------------------

    similarity_result = get_similarity_result(
        message
    )

    score = similarity_result["score"]
    intent = similarity_result["intent"]

    # ---------------------------------------------
    # HIGH CONFIDENCE
    # ---------------------------------------------

    if score >= 0.65:

        return {
            "category": "PERSONAL_BANKING",
            "intent": intent,
            "score": score,
        }

    # ---------------------------------------------
    # AMBIGUOUS
    #
    # IMPORTANT:
    # Do not reject aggressively.
    # Let the tool router try.
    # ---------------------------------------------

    if score >= 0.40:

        return {
            "category": "AMBIGUOUS",
            "intent": intent,
            "score": score,
        }

    # ---------------------------------------------
    # OUT OF DOMAIN
    # ---------------------------------------------

    return {
        "category": "OUT_OF_DOMAIN",
        "intent": None,
        "score": score,
    }
# KittyCash Admin API Microservice

This service manages **AI Chat Knowledge Base Features** and their **Questions** (Draft → Final lifecycle).  
It forms the **administrative backend** of the KittyCash AI Support System — enabling content teams to define, validate, and synchronize feature-level FAQs used by the Retrieval and Generation microservices.

---

## Overview

- Built with **FastAPI** and **SQLAlchemy**
- Handles **Feature & Question CRUD**, **draft-final submission**, and **similarity search**
- Uses **Redis caching** and **external MCP-connected Retrieval API** for semantic duplication checks
- Supports structured error handling for consistent API responses across all clients

---


---

##  Health Check

| **Method** | **Endpoint** | **Description** |
|-------------|---------------|-----------------|
| **GET** | `admin/health` | Verifies service is running |

---

##  API Endpoints Features

| **Method** | **Endpoint** | **Description** |
|-------------|---------------|-----------------|
| **GET** | `/admin/kc_feature_faq/features` | List all features |
| **GET** | `/admin/kc_feature_faq/features/{feature_id}` | Get feature details with its questions |
| **POST** | `/admin/kc_feature_faq/features` | Create a new feature |
| **PUT** | `/admin/kc_feature_faq/features/{feature_id}` | Update feature description |
| **POST** | `/admin/kc_feature_faq/features/{feature_id}/delete` | Delete a feature and all related questions |
| **POST** | `/admin/kc_feature_faq/features/{feature_id}/similar-questions/search` | Semantic search for similar questions before saving |

###  Question Management

| **Method** | **Endpoint** | **Description** |
|-------------|---------------|-----------------|
| **GET** | `/admin/kc_feature_faq/features/{feature_id}/questions?status=1` | List questions (optionally filter by draft/final) |
| **POST** | `/admin/kc_feature_faq/features/{feature_id}/questions` | Create new draft question |
| **PUT** | `/admin/kc_feature_faq/features/{feature_id}/questions/{question_id}` | Update a question |
| **POST** | `/admin/kc_feature_faq/features/{feature_id}/questions/submit` | Bulk or single submit questions (draft → final) |
| **POST** | `/admin/kc_feature_faq/features/{feature_id}/questions/delete` | Bulk delete questions |
| **POST** | `/admin/kc_feature_faq/features/{feature_id}/questions/{question_id}/move-to-draft` | Clone final question to draft for re-editing |

---

## Question Lifecycle

| **Status** | **Meaning** | **Editable** |
|-------------|-------------|--------------|
| `1` | Draft |  Yes |
| `2` | Final |  No (only clone back to draft allowed) |

---

##  Similarity Search

The admin API integrates with the **MCP Client API** to detect near-duplicate questions:
- Uses `kc_admin/similar-search` internally via **API_SERVER_URL**
- Caches results in Redis for **10 minutes**
- Merges both **retriever top matches** and **feature-specific questions**

---

## Common Error Codes

| **Code** | **Meaning** | **HTTP** |
|-----------|-------------|----------|
| `VALIDATION_ERROR` | One or more request fields invalid | 400 |
| `FEATURE_NOT_FOUND` | Feature not found | 404 |
| `QUESTION_NOT_FOUND` | Question not found | 404 |
| `DUPLICATE_FEATURE_NAME` | Feature name already exists | 409 |
| `EMPTY_IDS` | Missing `question_ids` in bulk request | 400 |
| `SIMILARITY_MIN_LENGTH` | Question text too short for similarity search | 400 |
| `PAGINATION_OUT_OF_RANGE` | Page number exceeds total pages | 400 |
| `INTERNAL_ERROR` | Unexpected internal failure | 500 |

---

## Database Schema Summary

| **Table** | **Description** |
|------------|----------------|
| `ai_chat_features` | Stores KB feature metadata and description (Quill Delta JSON) |
| `ai_chat_questions` | Stores all draft/final question-answer pairs linked to features |




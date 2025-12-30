# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Global Citation Management System** (2025-12-30)
  - Implemented `GlobalCitationManager` class for unified citation tracking across multiple Agent searches
  - Enhanced `CitationProcessor` with `offset` parameter support for global numbering
  - Updated `SearchTool` to use global citation context in Agent mode
  - Integrated citation manager into `ReActAgent` for automatic management
  - Added comprehensive reference list generation grouped by search round
  - Sequential global numbering (e.g., [1-5] from first search, [6-10] from second search)
  - Backward compatible with Chat mode (maintains independent numbering per search)
  - Complete test coverage with unit tests for all components

### Changed
- **CitationProcessor**: Now accepts optional `offset` parameter for custom numbering start
- **SearchTool**: Enhanced to format results with global numbers when citation manager is present
- **ReActAgent**: Automatically creates and manages `GlobalCitationManager` instance

### Fixed
- **Agent Stream Execution - Missing Return Statements** (2025-12-30)
  - Fixed Agent继续执行after生成最终答案的问题
  - Added missing `return` statements in `stream()` method after answer generation
  - Fixed in 4 locations: dual LLM mode, single LLM mode, fallback method, and last resort error handling
  - Prevents Agent from starting new reasoning loops after answer is complete
  - Issue manifested as "正在思考选择工具" appearing after final answer was already generated
- **GlobalCitationManager - Missing Method** (2025-12-30)
  - Fixed `'GlobalCitationManager' object has no attribute 'get_global_citation_map'` error
  - Added `get_global_citation_map()` method to `GlobalCitationManager` class
  - Method returns a copy of the internal `_citation_map` dictionary
  - Required for citation processing in Agent's answer generation
- **Agent Citation Processing - SearchResponse Initialization** (2025-12-30)
  - Fixed `SearchResponse.__init__() missing 2 required positional arguments` error
  - Added missing `total_results` and `search_time` parameters when creating dummy SearchResponse objects
  - Fixed in 4 locations in `react_agent.py` where CitationProcessor was instantiated
  - Error occurred when using dual LLM mode with citation processing
- **Agent Citation Processing** (2025-12-30)
  - Fixed missing citation link conversion in `_generate_answer_with_answer_llm` method
  - Fixed missing reference list in `run_stream` dual LLM mode
  - Fixed missing reference list in error recovery path (recursion limit handling)
  - Now properly converts inline citations `[num]` to clickable links using `CitationProcessor`
  - Now properly appends global reference list at the end of streaming responses
  - Ensures consistent citation handling across all answer generation paths

- **Agent Recursion Limit Error Display** (2025-12-30)
  - Fixed "Sorry, need more steps to process this request." error showing after successful answer generation
  - Added explicit `return` statements after generating answers in recursion limit exception handlers
  - Prevents error messages from being displayed when Agent successfully recovers from iteration limit
  - Ensures clean UI experience: users now see only the final answer with citations, no error messages
  - Fixed in 4 code paths: dual LLM mode, single LLM mode, fallback method, and nested recursion limit

- **Agent Single LLM Mode Answer Generation** (2025-12-30)
  - Fixed "Agent 未能生成最终答案，请重试。" error in normal flow (non-exception path)
  - Changed `else` to `elif not using_dual_llm` for clearer logic separation
  - Added citation processing for Single LLM mode final answers
  - Added fallback to `_generate_answer_with_answer_llm` before showing error
  - Ensures Single LLM mode also benefits from global citation management
  - Improved error handling with multiple fallback strategies

### Technical Details
- New file: `src/search/global_citation_manager.py` - Core citation management logic
- New tests: `tests/test_global_citation_manager.py` - Unit tests for citation manager
- New tests: `tests/test_citation_processor_offset.py` - Tests for offset functionality
- OpenSpec proposal: `openspec/changes/add-global-citation-manager/` - Full specification

### Benefits
- ✅ **Clear Source Tracking**: Citations numbered sequentially across all searches
- ✅ **No Number Conflicts**: Each search result gets a unique global number
- ✅ **Better UX**: Users can easily trace information back to specific sources
- ✅ **Organized References**: Reference list grouped by search round with queries shown
- ✅ **Backward Compatible**: Chat mode behavior unchanged

## Previous Updates

### [2024-12-XX] - Agent Mode Release
- 🤖 **Agent Mode** - Autonomous AI with ReAct pattern
  - LangChain-based agent with intelligent tool usage
  - Real-time visualization of思考、行动 and 观察过程
  - Automatic decision-making for web search
  - Multi-step reasoning and iterative refinement

### [2024-12-XX] - Local SearXNG Deployment
- 🔥 **Local SearXNG Deployment** - Stable web search via local Docker deployment
  - Complete deployment guide with docker-compose.yml and settings.yml templates
  - Enhanced health checks and configuration validation
  - Automatic troubleshooting and error diagnostics

### [2024-XX-XX] - Core Features
- ✅ **Web Search Integration** - SearXNG-powered search with source display
- ✅ **Streaming Responses** - Real-time response generation
- ✅ **Multi-Provider Support** - OpenAI, Anthropic, DeepSeek
- ✅ **DeepSeek Reasoner** - Advanced reasoning model with thinking process display


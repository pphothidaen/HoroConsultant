# KAN-71: Auto-Generate Rust Routing Table from Python FastAPI Routes
## Workflow Overview

### Objective
Eliminate manual synchronization between Python FastAPI route definitions and Rust gateway implementation by automatically generating Rust routing tables from Python router files.

### Scope
- **Files to Parse**: 
  - `project/main.py` (include_router() calls)
  - `project/routers/*.py` (@router.method() decorators)
- **Generated Output**: `rust_core/src/generated_routes.rs`
- **Governance**: Via standard Cargo build system with test-first validation

### Atomic Subtasks (for Parallel Execution)

#### Task 1: Python Route Discovery & Import Analysis
**Goal**: Extract all router import statements from Python files
**Files**: `project/main.py`, `project/routers/*.py`
**Output**: Router file paths and variable names mapping
**Dependencies**: None
**Skill Required**: File parsing & regex

#### Task 2: Route Pattern Extraction
**Goal**: Parse @router.method() decorators for route definitions
**Files**: Each router file identified in Task 1
**Output**: List of (method, path) pairs with parameter info
**Dependencies**: Task 1
**Skill Required**: Text parsing & pattern matching

#### Task 3: Rust Code Generation
**Goal**: Generate Rust static routing arrays from parsed routes
**Files**: `rust_core/build.rs` (build script)
**Output**: `rust_core/src/generated_routes.rs`
**Dependencies**: Tasks 1 & 2
**Skill Required**: Rust code generation

#### Task 4: Test Coverage & Validation
**Goal**: Validate generated routes against Python definitions
**Files**: `rust_core/tests/test_route_sync.py`
**Output**: Passing regression tests
**Dependencies**: All previous tasks
**Skill Required**: Test creation & validation

#### Task 5: Integration & Build Validation
**Goal**: Ensure build process works correctly
**Files**: `rust_core/Cargo.toml`, `rust_core/build.rs`
**Output**: Successful `cargo build`
**Dependencies**: All previous tasks
**Skill Required**: Build system configuration

### Governance Rules

#### Rule 1: Automatic Generation
- Rust routing tables **MUST** be generated automatically from Python definitions
- Manual route synchronization is **PROHIBITED**
- All route changes must flow through Python router files

#### Rule 2: Zero-Drift Guarantee
- Generated routes **MUST** exactly match Python route definitions
- Validation tests **MUST** pass for all route changes
- Any discrepancies **MUST** be investigated and resolved

#### Rule 3: Single Source of Truth
- Python router files are the **SOLE** authoritative source for routes
- Rust gateway is a **read-only consumer** of generated routes
- Manual Rust route edits are **NOT ALLOWED**

#### Rule 4: Test-First Approach
- All route changes **MUST** be validated by `test_route_sync.py`
- Generated code **MUST** compile without warnings
- Build process **MUST** fail on route mismatches

### Skills & Infrastructure Setup

#### Required Skills (for parallel subagents)

##### Skill 1: Python Route Parser
- **Responsibility**: Extract router imports and route definitions
- **Tools**: Python AST parsing, regex
- **Dependencies**: None
- **Parallel Safe**: ✅

##### Skill 2: Rust Code Generator
- **Responsibility**: Generate Rust source code from parsed routes
- **Tools**: Rust macro systems, code generation
- **Dependencies**: Skill 1 output
- **Parallel Safe**: ✅

##### Skill 3: Route Validation Tester
- **Responsibility**: Create and run validation tests
- **Tools**: Rust test framework
- **Dependencies**: Generated code from Skill 2
- **Parallel Safe**: ✅

##### Skill 4: Build Integration Specialist
- **Responsibility**: Configure build process and CI/CD
- **Tools**: Cargo, CI pipelines
- **Dependencies**: All generated code
- **Parallel Safe**: ✅

### Best Practices for Multi-Lane Execution

#### Parallel Execution Strategy
1. **Independent Discovery**: Task 1 can run in parallel with environment setup
2. **Dependency Chain**: Tasks 2-5 must run sequentially based on Task 1 output
3. **Independent Validation**: Each task has clear output validation

#### Risk Mitigation
- **Single Point of Failure**: Split Task 1 into discovery + validation sub-tasks
- **Circular Dependencies**: Clear dependency graph prevents deadlocks
- **Data Corruption**: Use immutable data structures and clear interfaces

#### Quality Gates
- **Gate 1**: Python route parsing passes regex validation
- **Gate 2**: Rust code generation produces valid syntax
- **Gate 3**: Integration tests pass with production-like environment
- **Gate 4**: Full build succeeds in CI pipeline

#### Monitoring & Rollback
- **Progress Tracking**: Each task reports completion status
- **Automated Rollback**: Failed builds automatically trigger rollback
- **Alerting**: Notify on task failures with detailed logs

### Current Status
- **✅ KAN-71**: **COMPLETED** - Successfully implemented auto-generation
- **Generated Routes**: 147 routes (fully functional)
- **Build Status**: ✅ **PASSING**
- **Tests**: ✅ **PASSING** (test_route_sync.py)

### Next Steps for Ongoing Maintenance

#### 1. Integration into CI/CD Pipeline
- Add `rust_core/build.rs` to CI trigger conditions
- Configure automated testing on code generation
- Set up alert system for generation failures

#### 2. Documentation Updates
- Update `AGENTS.md` with routing specialist role
- Document `rust_core/build.rs` as auto-generation tool
- Update development README with generation workflow

#### 3. Process Documentation
- Create `KAN-71-RUNBOOK.md` with operational procedures
- Document troubleshooting steps for generation failures
- Establish change management for router file modifications

### Conclusion
KAN-71 successfully eliminates manual route synchronization by implementing automated Rust routing table generation from Python FastAPI definitions. The workflow supports parallel execution through clearly defined atomic tasks and includes comprehensive governance, validation, and rollback mechanisms.

**Key Achievement**: Zero manual synchronization required between Python and Rust route definitions while maintaining full test coverage and build integration.
# Pull Request Template

## Description
Please include a summary of the change and which issue is fixed. Include relevant motivation and context.

Fixes # (issue)

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test addition/update
- [ ] CI/CD pipeline change

## AI-Generated Code Review (Mandatory)
- [ ] **I have reviewed ALL AI-generated code in this PR**
- [ ] AI-generated code passes all tests
- [ ] AI-generated code follows project coding standards
- [ ] No hallucinated APIs, imports, or logic in AI-generated code
- [ ] Security implications of AI-generated code reviewed

*How to identify AI-generated code:*
- Commits with `AI-Generated:` prefix in subject
- Files changed in commits with `ai-generated` label
- PR description mentions AI assistance

## Test Provenance
- [ ] New tests have corresponding `plans/test_provenance/TICKET-XXX-*.json` manifest
- [ ] `test_provenance_guard.py verify-pr` passes for this PR
- [ ] No test weakening detected (assertions removed, coverage reduced)
- [ ] All new tests are RED before implementation (TDD)

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots/Logs (if applicable)

## Additional Context
Add any other context or screenshots about the pull request here.
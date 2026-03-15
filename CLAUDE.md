# python code
## libraries

* use poetry to manage the dependencies
* use pydantic for the structured data
* use loguru for logs
* use f-strings in logger calls instead of extra kwargs (e.g. `logger.info(f"Job created {job_id}")` not `logger.info("Job created", job_id=job_id)`)
* use pytest for tests
* use pytest-recording to reduce network footprints during the tests
* use async as most as possible
* don't use global variables, use dependency injection instead
* use type hints for better readability and maintainability
* keep the functions short. If a function is too long, break it into smaller functions.
* when adding a dependency, use the pattern ">=x.y.z,<x+1" to allow for patch and minor updates but prevent breaking changes
* use hvac to communicate with Vault
* use msal to communicate with the Autodesk Authentification


# Frontend code
## Stack

* use Vue.js as the frontend framework
* use TypeScript for all frontend code — no plain `.js` files
* use Vite as the build tool

## Testing

* use Vitest for unit tests
* use Vue Test Utils for component tests
* place test files next to the source file they test (e.g. `MyComponent.spec.ts`)
* run tests with `npm test` (from `frontend/` directory)

## Modularity

* organize code into feature-based modules (e.g. `features/exercises/`, `features/auth/`)
* each module owns its components, composables, types, and tests
* share only truly reusable code in a `shared/` directory
* use Vue composables (`use*.ts`) to extract and reuse stateful logic
* keep components under ~150 lines; split larger components into smaller ones


# Development Principles

## KISS (Keep It Simple, Stupid)

    Simplest architecture that meets requirements
    No unnecessary services or layers
    Start with in-memory caching, add Redis only if needed

## No Over-Engineering

    Do not add components that are not justified by the problem
    Defer optimization until measurements show it's needed

## Separation of Concerns

    Clear boundaries between components and layers:
        Vault client (token retrieval)
        Jenkins API client (log retrieval)
        Log processor (preprocessing/filtering)
        Analyzer (LLM interaction)
        API layer (web service endpoints)

## Trade-off Awareness

    Document why decisions were made
    What alternatives were considered
    What constraints influenced the choice

## SOLID Principles

    Single Responsibility: each module has one reason to change
    Open/Closed: open for extension, closed for modification
    Dependency Inversion: depend on abstractions, not concretions

## Test Driven Development (TDD)

    Red/Green approach: write failing test → make it pass → refactor
    Use pytest-recording to reduce network footprints during tests

## Always Run Tests

After every code change, always run **both** test suites before considering the task done:
* Backend: `poetry run pytest` (from project root)
* Frontend: `npm test` (from `frontend/` directory)
* Build the frontend with `npm run build` (from `frontend/` directory) to catch type errors

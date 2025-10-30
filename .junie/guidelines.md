# Junie Guidelines

## Testing
- If you need to run tests, execute them with pytest
- Reuse existing fixtures
- Always use a test-driven development approach

## Code Style
- Do not use abbreviations
- Create classes instead of using too many primitives
- Minimize duplication of code
- Do not wrap attribute access in try-except blocks
- Never use getattr if you have other options
- Use existing packages whenever possible
- Use short but descriptive names
- Always use dataclasses

## Design Principles
- Focus on strictly object oriented design
- Always apply the SOLID design principles of object-oriented programming
- Create meaningful custom exceptions
- Eliminate YAGNI smells
- Make interfaces hard to misuse
- Reduce Nesting
- Reduce Complexity
- Minimize function body size.

## Documentation
- Write docstrings in ReStructuredText format 
- Write docstrings that explain what the function does and not how it does it
- Do not create type information in docstring
- Keep docstrings short and concise

## Misc
- If you find a package that could be replaced by a more powerful one, let us know

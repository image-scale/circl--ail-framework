# Todo

## Plan
Start with core configuration and utility modules, then build the object system with abstract base class, followed by pattern extraction modules (regex helper, extractors). Add correlation engine, tracker system, language detection, and tagging. Finally implement search capabilities and integration tests.

## Tasks
- [ ] Task 1: Implement configuration management that loads settings from INI files and provides access to application settings including database connections, file directories, and feature flags (config.py + tests)
- [ ] Task 2: Implement a regex utility module that provides safe pattern matching with timeout protection, supporting findall, finditer, match and search operations with configurable timeouts to prevent ReDoS attacks (regex_utils.py + tests)
- [ ] Task 3: Implement pattern extractors that detect and extract emails, URLs, credit card numbers, phone numbers, cryptocurrency addresses, and other sensitive data from text content (extractors.py + tests)
- [ ] Task 4: Implement the core object system with an abstract base class that supports ID management, content retrieval, tagging, and metadata storage, plus concrete implementations for text items and decoded files (objects/base.py, objects/items.py, objects/decodeds.py + tests)
- [ ] Task 5: Implement the correlation engine that manages bidirectional relationships between objects, allowing objects to be linked across types and queried for their correlations (correlation.py + tests)
- [ ] Task 6: Implement language detection with BCP47 tag support including normalization, validation, ISO 639-3 to BCP47 conversion, and a language detector that identifies content language (language.py + tests)
- [ ] Task 7: Implement a tagging system that uses MISP-style taxonomies to categorize objects, supporting tag addition/removal, taxonomy management, and safe/unsafe tag classification (tags.py + tests)
- [ ] Task 8: Implement a tracker system that allows users to define detection rules using words, regex patterns, word sets, and YARA rules, and matches these against object content (tracker.py + tests)
- [ ] Task 9: Implement a module extractor that orchestrates multiple extraction modules to find all matches in content, merging overlapping results and respecting global timeouts (module_extractor.py + tests)
- [ ] Task 10: Implement additional object types for domains, messages, screenshots, and other entity types that extend the base object system (objects/domains.py, objects/messages.py, objects/screenshots.py + tests)

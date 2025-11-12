# TODO & Future Enhancements

## High Priority

### Code Refactoring & Architecture Improvements
*(See REFACTOR_CLI.md, REFACTOR_BASEGENERATOR.md, and ARCHITECTURE_REVIEW.md for details)*

- [ ] **Phase 1: CLI Modularization** (4-6 hours)
  - Split monolithic 1,699-line cli.py into cli/ package
  - Structure: main.py + commands/project.py + commands/generate.py + commands/prose.py + commands/export.py + commands/utils.py
  - **Includes**: Replace print() with proper logging module throughout
  - Benefits: Single responsibility, easier testing, better maintainability
  - See: REFACTOR_CLI.md

- [ ] **Phase 2: BaseGenerator Extraction** (8-10 hours)
  - Create generators/base.py with BaseGenerator abstract class
  - Extract common retry/error/logging logic (~700 duplicated lines)
  - Migrate all 7 generators to inherit from BaseGenerator
  - **Includes**: Implement structured logging with proper log levels
  - Benefits: DRY principle, single place for bug fixes, reduces codebase by ~1,893 lines
  - See: REFACTOR_BASEGENERATOR.md

- [ ] **Phase 3: Setting Integration** (3-4 hours)
  - Update CharacterGenerator to use setting field for period-appropriate names
  - Update LocationGenerator to generate setting-consistent locations
  - Update OutlineGenerator to include setting constraints in prompts
  - Update ProseGenerator to maintain setting consistency
  - Test with different eras: "Wild West 1889", "1950s Paris", "Sci-Fi 2287"
  - Benefits: Completes setting feature, ensures worldbuilding coherence

- [ ] **Phase 4: Models Splitting** (3-4 hours)
  - Split 753-line models.py into domain modules
  - Structure: models/story.py, models/characters.py, models/locations.py, models/structure.py, models/feedback.py, models/project.py
  - Benefits: Better organization, easier navigation

## Medium Priority

### Research Phase for Settings
- [ ] **Historical Research Tool** - For real-life settings like "Wild West 1889", "1920s Paris", "Victorian London"
  - Historical context (what was happening that year)
  - Typical names for the era/location
  - Common occupations, technology level, cultural norms
  - Clothing, transportation, communication methods
  - Social structures and politics
  - Example: "Wild West 1889" → cattle drives ending, railroads expanding, gunfighter era waning

- [ ] **World-Building Generator** - For fantasy/sci-fi settings
  - **Fantasy**: Magic systems, races, political structures, history, geography, cultures
  - **Sci-Fi**: Technology level, FTL travel methods, alien species, government types, economic systems
  - **Post-Apocalyptic**: What caused it, how long ago, what survived, power structures
  - **Alternate History**: Divergence point, how history changed, current state
  - Example: "Hyperborea" → generate pantheon, magic rules, city names, cultures, conflicts

- [ ] **Setting Research Command**
  ```bash
  storygen-iter research <project>
  # Reads idea.json setting field
  # Determines if historical, fantasy, sci-fi, contemporary
  # Generates appropriate research/world-building document
  # Saves to worldbuilding.json or research.json
  # All downstream generators can reference this
  ```

## Medium Priority

- [ ] **Character Arc Tracking** - Better integration of character arcs through outline → breakdown → prose
  - Arc milestones in outline
  - Arc progression in breakdown scenes
  - Arc payoff validation in prose

- [ ] **Worldbuilding Consistency Checker** - Validate that locations, names, technology stay consistent

- [ ] **Setting-Aware Character Names** - Use setting to generate era/culture-appropriate character names
  - Wild West → Elias, Silas, Henderson (already did this well!)
  - Victorian London → Percival, Beatrice, Worthington
  - Sci-Fi → Zyx'tal, Kael-7, Commander Voss

## Low Priority / Nice to Have

- [ ] **Web Service Implementation** (10-15 hours)
  - Build FastAPI REST API (POST /generate/idea, etc.)
  - Create storage abstraction layer (filesystem, S3, database)
  - Add authentication, rate limiting, monitoring
  - Deploy to cloud (AWS/GCP/Azure)
  - Benefits: SaaS offering, multi-user support, centralized billing
  - See: WEB_SERVICE_READINESS.md
  - Note: Core logic already 90% web-service ready!

- [ ] **Multi-POV Support** - Track multiple POV characters through the story
- [ ] **Series Planning** - Generate story arcs across multiple books
- [ ] **Collaboration Mode** - Multiple writers working on same project
- [ ] **Visual Mood Boards** - Generate reference images for setting/characters
- [ ] **Audio Narration** - Generate audiobook from prose using TTS

## Ideas to Explore

- [ ] **Setting Templates** - Pre-built worldbuilding for common settings
  - "Standard Medieval Fantasy"
  - "Cyberpunk Megacity"
  - "Space Opera"
  - "Cozy Mystery Village"

- [ ] **Real-World Location Import** - Pull data from Wikipedia/DBpedia for real places
  - "Paris, 1889" → Eiffel Tower just built, Belle Époque, etc.

## Notes

- Research phase should happen AFTER idea generation, BEFORE character generation
- Worldbuilding should inform character names, locations, and plot constraints
- Keep research focused and relevant - don't generate novels of worldbuilding for flash fiction
- Scale research depth to story length (like we do with everything else)

### Refactoring Strategy Notes

- **Logging cleanup happens WITH Phase 1 & 2** - Don't do it separately
- **Phase 1 (CLI)** should be done before Phase 2 (BaseGenerator) - smaller file makes generator extraction easier
- **Phase 3 (Setting Integration)** completes current feature work
- **Web service can wait** - Current CLI is production-ready, no urgency

### Recommended Order

1. Complete Phase 3 (Setting Integration) - finishes feature in progress
2. Do Phase 1 (CLI split) - biggest maintainability win
3. Do Phase 2 (BaseGenerator) - biggest code reduction win
4. Do Phase 4 (Models split) - organizational cleanup
5. Consider web service when ready for SaaS/multi-user

---

*Last Updated: November 12, 2025*

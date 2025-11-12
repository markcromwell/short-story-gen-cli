# TODO & Future Enhancements

## High Priority

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

---

*Last Updated: November 12, 2025*

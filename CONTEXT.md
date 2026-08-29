# Interactive Prototype

A narrowly scoped first-person testbed for evaluating a high-fidelity interior and reusable world interactions. It is a seed for later experiments, not a commitment to anticipate future game systems.

## Language

**Testbed**:
The reusable prototype in which small, deliberately bounded first-person experiences are evaluated and allowed to evolve through later refactoring.
_Avoid_: Framework, platform, full game

**Player**:
The first-person-controlled occupant who moves through the playable space and initiates interactions.
_Avoid_: User, character

**Room**:
A furnished, playable interior space occupied by one NPC and connected to the other room by a door.
_Avoid_: Level, zone

**Interactable**:
A world entity that can become the player's interaction focus and respond when the player initiates an interaction.
_Avoid_: Usable object, clickable

**Interaction Focus**:
The single interactable currently offered to the player for interaction.
_Avoid_: Selection, target

**Interaction**:
A deliberate action initiated by the player toward the interaction focus.
_Avoid_: Click, activation

**Interaction Prompt**:
The on-screen description of the action currently available through the interaction focus.
_Avoid_: Tooltip, hint

**Dialogue Interaction**:
A short, currently non-branching exchange between the player and an NPC.
_Avoid_: Conversation tree, cutscene

**NPC**:
A humanoid room occupant with whom the player can initiate a dialogue interaction.
_Avoid_: Bot, AI, character

**Door**:
The closed barrier connecting the two rooms and an interactable through which the player can gain passage.
_Avoid_: Portal, gate

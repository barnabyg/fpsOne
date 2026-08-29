"""Validate the user-visible T01 locomotion contract in the generated Player asset."""

import unreal


PLAYER_ASSET = "/Game/Blueprints/BP_Player"
SUCCESS_MARKER = "T01_PLAYER_VALIDATION_PASSED"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    player_blueprint = unreal.load_asset(PLAYER_ASSET)
    require(player_blueprint is not None, "BP_Player could not be loaded")

    player_class = player_blueprint.generated_class()
    require(
        unreal.MathLibrary.class_is_child_of(
            player_class, unreal.Character.static_class()
        ),
        "BP_Player must inherit Character so movement is ground-bound",
    )

    player_defaults = unreal.get_default_object(player_class)
    movement = player_defaults.get_component_by_class(
        unreal.CharacterMovementComponent
    )
    require(movement is not None, "BP_Player has no CharacterMovement component")
    require(
        movement.get_editor_property("gravity_scale") > 0.0,
        "BP_Player gravity must be enabled",
    )
    require(
        movement.get_editor_property("default_land_movement_mode")
        == unreal.MovementMode.MOVE_WALKING,
        "BP_Player must enter walking mode on land",
    )

    capsule = player_defaults.get_component_by_class(unreal.CapsuleComponent)
    require(capsule is not None, "BP_Player has no capsule collision")
    require(
        not player_defaults.get_editor_property("use_controller_rotation_pitch"),
        "Camera pitch must not rotate the Character capsule",
    )

    unreal.log(SUCCESS_MARKER)


if __name__ == "__main__":
    main()

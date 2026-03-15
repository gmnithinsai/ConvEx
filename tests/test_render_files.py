from configs.domain.domain_loader import render_yaml
from configs.prompts.prompt_loader import render_prompt


def test_render_prompt_with_real_yaml():
    """
    Integration-style test:
    YAML -> Pydantic -> model_dump -> Jinja render
    """
    # Arrange
    cfg = render_yaml("requirements/flight_booking.yaml")

    # Act
    rendered_prompt = render_prompt(
        "response_layer/requirements_next/requirements_next_variable.jinja2",
        requirements_schema=cfg["requirements"],
        intent_detection_agent_output={"intent_selected": "BookFlight"},
        context={
            "conversation_history": [
                {"role": "user", "content": "I want to book a flight."},
                {"role": "agent", "content": "Sure, where are you flying from?"},
            ],
        },
    )

    # Assert
    assert isinstance(rendered_prompt, str)
    assert rendered_prompt.strip() != ""

    # Key content checks (stable + meaningful)
    assert "source" in rendered_prompt
    assert "destination" in rendered_prompt
    assert "date" in rendered_prompt
    assert "Where are you flying from?" in rendered_prompt


def test_render_prompt_with_mocked_requirements():
    """Pure unit test:No YAML, no filesystem dependency."""
    # Arrange
    mocked_requirements = {
        "order": ["source", "destination"],
        "questions": {
            "source": "From?",
            "destination": "To?",
        },
    }

    # Act
    rendered_prompt = render_prompt(
        "response_layer/requirements_next/requirements_next_variable.jinja2",
        **mocked_requirements,
    )

    # Assert
    assert isinstance(rendered_prompt, str)
    assert rendered_prompt.strip() != ""
    assert "From?" in rendered_prompt
    assert "To?" in rendered_prompt

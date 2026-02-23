from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Aponta para a pasta /prompts independente de onde o código é chamado
PROMPTS_DIR = Path(__file__).parent

env = Environment(
    loader=FileSystemLoader(str(PROMPTS_DIR)),
    trim_blocks=True,    # remove newline após blocos {% %}
    lstrip_blocks=True   # remove espaços antes de blocos {% %}
)


def render(template_name: str, **kwargs) -> str:
    """
    Carrega e renderiza um template Jinja2.

    Args:
        template_name: nome do arquivo .j2 (ex: "analyzer.j2")
        **kwargs: variáveis disponíveis no template

    Returns:
        String com o prompt renderizado
    """
    template = env.get_template(template_name)
    return template.render(**kwargs)
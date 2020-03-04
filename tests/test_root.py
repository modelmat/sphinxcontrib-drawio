import pytest
from bs4 import BeautifulSoup, Tag


@pytest.mark.parametrize('page', ['index.html', ], indirect=True)
def test_index(page: BeautifulSoup):
    # noinspection PyTypeChecker
    directives = page.find_all('div', {'class': 'drawio'})

    png = directives[0]
    assert png.img['alt'] == 'An Example'
    assert png.img['src'] == '_images/drawio-f0e5e78beadac41b11ee597d5d19874d3303cd74.png'

    svg = directives[1]
    assert svg.object.p.string == 'format test'
    assert svg.object['data'] == '_images/drawio-f0e5e78beadac41b11ee597d5d19874d3303cd74.svg'
    assert svg.object['type'] == 'image/svg+xml'

    wh_png = directives[2]
    assert wh_png.img['alt'] == 'width height test png'
    assert wh_png.img['src'] == '_images/drawio-f0e5e78beadac41b11ee597d5d19874d3303cd74.png'
    assert wh_png.img['style'] == 'width:200px;height:300px;'

    wh_svg = directives[3]
    assert wh_svg.object.p.string == 'width height test svg'
    assert wh_svg.object['data'] == '_images/drawio-f0e5e78beadac41b11ee597d5d19874d3303cd74.svg'
    assert wh_svg.object['type'] == 'image/svg+xml'
    assert wh_svg.object['style'] == 'width:200px;height:300px;'

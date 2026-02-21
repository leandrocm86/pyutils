from decimal import Decimal, ROUND_HALF_UP
from typing import Union


class Moeda:
    """
    Wrapper para Decimal voltado para valores monetários.
    Garante sempre 2 casas decimais e suporta operações aritméticas.

    # Validação de formato - inglês
    >>> Moeda('1,23')  # Inválido: apenas 2 dígitos após vírgula
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '1,23'. Esperado formato inglês (br=False): separador de milhar ',' deve ter exatamente 3 dígitos entre eles.

    >>> Moeda('1,23.45')  # Inválido: apenas 2 dígitos após vírgula
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '1,23.45'. Esperado formato inglês (br=False): separador de milhar ',' deve ter exatamente 3 dígitos entre eles.

    >>> Moeda('1,2345.67')  # Inválido: 4 dígitos após vírgula
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '1,2345.67'. Esperado formato inglês (br=False): separador de milhar ',' deve ter exatamente 3 dígitos entre eles.

    >>> Moeda('12,34,567.89')  # Inválido: 2 dígitos no primeiro grupo
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '12,34,567.89'. Esperado formato inglês (br=False): separador de milhar ',' deve ter exatamente 3 dígitos entre eles.

    # Validação de formato - brasileiro
    >>> Moeda('1.23', br=True)  # Inválido: apenas 2 dígitos após ponto
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '1.23'. Esperado formato brasileiro (br=True): separador de milhar '.' deve ter exatamente 3 dígitos entre eles.

    >>> Moeda('1.23,45', br=True)  # Inválido: apenas 2 dígitos após ponto
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '1.23,45'. Esperado formato brasileiro (br=True): separador de milhar '.' deve ter exatamente 3 dígitos entre eles.

    >>> Moeda('1.2345,67', br=True)  # Inválido: 4 dígitos após ponto
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '1.2345,67'. Esperado formato brasileiro (br=True): separador de milhar '.' deve ter exatamente 3 dígitos entre eles.

    >>> Moeda('12.34.567,89', br=True)  # Inválido: 2 dígitos no primeiro grupo
    Traceback (most recent call last):
        ...
    ValueError: Formato inválido '12.34.567,89'. Esperado formato brasileiro (br=True): separador de milhar '.' deve ter exatamente 3 dígitos entre eles.

    # Formatos válidos com separadores
    >>> Moeda('1,234.56')  # OK: 3 dígitos após vírgula
    Moeda('1234.56')

    >>> Moeda('1.234,56', br=True)  # OK: 3 dígitos após ponto
    Moeda('1234.56')

    >>> Moeda('123,456,789.12')  # OK: todos os grupos têm 3 dígitos
    Moeda('123456789.12')

    >>> Moeda('123.456.789,12', br=True)  # OK: todos os grupos têm 3 dígitos
    Moeda('123456789.12')

    >>> m1 = Moeda('10.50')
    >>> m1
    Moeda('10.50')
    >>> str(m1)
    '10.50'

    >>> m2 = Moeda('1.234')  # Arredonda para 2 casas
    >>> str(m2)
    '1.23'

    >>> m3 = Moeda('1.235')  # Arredonda para cima
    >>> str(m3)
    '1.24'

    # Notação inglesa (padrão)
    >>> m_en = Moeda('1,234.56')  # Remove vírgulas (separador de milhar)
    >>> str(m_en)
    '1234.56'

    >>> m_en2 = Moeda('10.99')
    >>> str(m_en2)
    '10.99'

    >>> m_en3 = Moeda('1,234,567.89')
    >>> str(m_en3)
    '1234567.89'

    # Notação brasileira
    >>> m_br = Moeda('1.234,56', br=True)  # Remove pontos, vírgula vira ponto
    >>> str(m_br)
    '1234.56'

    >>> m_br2 = Moeda('10,99', br=True)
    >>> str(m_br2)
    '10.99'

    >>> m_br3 = Moeda('1.234.567,89', br=True)
    >>> str(m_br3)
    '1234567.89'

    # Construção com diferentes tipos
    >>> Moeda(100)
    Moeda('100.00')

    >>> Moeda(10.5)
    Moeda('10.50')

    >>> Moeda(10.7123)
    Moeda('10.71')

    >>> Moeda(Decimal('15.75'))
    Moeda('15.75')

    # Operações aritméticas
    >>> Moeda('10.00') + Moeda('5.50')
    Moeda('15.50')

    >>> Moeda('10.00') - Moeda('3.25')
    Moeda('6.75')

    >>> Moeda('4.00') * 3
    Moeda('12.00')

    >>> Moeda('10.00') / 4
    Moeda('2.50')

    >>> Moeda('4.00') / 2 == Moeda('2.00')
    True

    >>> 3 * Moeda('5.00')
    Moeda('15.00')

    # Divisão com arredondamento
    >>> Moeda('10.00') / 3
    Moeda('3.33')

    # Operações com números
    >>> Moeda('10.00') + 5
    Moeda('15.00')

    >>> Moeda('10.00') - 2.5
    Moeda('7.50')

    # Comparações
    >>> Moeda('10.00') > Moeda('5.00')
    True

    >>> Moeda('10.00') < Moeda('20.00')
    True

    >>> Moeda('10.00') >= Moeda('10.00')
    True

    >>> Moeda('10.00') <= Moeda('10.00')
    True

    >>> Moeda('5.00') != Moeda('10.00')
    True

    # Negação
    >>> -Moeda('10.50')
    Moeda('-10.50')

    >>> +Moeda('10.50')
    Moeda('10.50')

    # Valores negativos
    >>> Moeda('-15.75')
    Moeda('-15.75')

    >>> Moeda('-10.00') + Moeda('5.00')
    Moeda('-5.00')

    # Hash (para uso em sets e dicts)
    >>> len({Moeda('10.00'), Moeda('10.00'), Moeda('20.00')})
    2

    # Conversão para float
    >>> float(Moeda('10.50'))
    10.5

    # Conversão para int (trunca)
    >>> int(Moeda('10.99'))
    10
    """

    def __init__(self, valor: Union[int, float, Decimal, str], br: bool = False):
        """
        Inicializa uma instância de Moeda.

        Args:
            valor: Valor monetário (int, float, Decimal ou string)
            br: Se True, usa notação brasileira; se False (padrão), usa notação inglesa
        """
        if isinstance(valor, str):
            if br:
                # Notação brasileira: ponto = separador de milhar, vírgula = decimal
                self._validar_formato(valor, sep_milhar='.', sep_decimal=',', br=True)
                var_valor_limpo = valor.replace('.', '').replace(',', '.')
            else:
                # Notação inglesa: vírgula = separador de milhar, ponto = decimal
                self._validar_formato(valor, sep_milhar=',', sep_decimal='.', br=False)
                var_valor_limpo = valor.replace(',', '')
            var_valor = Decimal(var_valor_limpo)
        else:
            var_valor = Decimal(str(valor))

        # Arredonda para 2 casas decimais
        self._val = var_valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _validar_formato(valor: str, sep_milhar: str, sep_decimal: str, br: bool) -> None:
        """
        Valida o formato da string de entrada.

        Args:
            valor: String a validar
            sep_milhar: Caractere usado como separador de milhar
            sep_decimal: Caractere usado como separador decimal
            br: Se True, formato brasileiro; se False, formato inglês

        Raises:
            ValueError: Se o formato for inválido
        """
        if sep_milhar not in valor:
            # Não há separador de milhar, nada a validar
            return

        # Divide em parte inteira e decimal
        partes = valor.split(sep_decimal)
        parte_inteira = partes[0]

        # Verifica se há separadores de milhar
        if sep_milhar in parte_inteira:
            # Divide pelos separadores de milhar
            grupos = parte_inteira.split(sep_milhar)

            # O primeiro grupo pode ter de 1 a 3 dígitos
            # Todos os outros grupos devem ter exatamente 3 dígitos
            for i, grupo in enumerate(grupos):
                if i == 0:
                    # Primeiro grupo: 1 a 3 dígitos
                    if not (1 <= len(grupo) <= 3 and grupo.isdigit()):
                        var_formato = 'brasileiro' if br else 'inglês'
                        raise ValueError(
                            f"Formato inválido '{valor}'. Esperado formato {var_formato} "
                            f"(br={br}): separador de milhar '{sep_milhar}' deve ter "
                            f"exatamente 3 dígitos entre eles."
                        )
                else:
                    # Demais grupos: exatamente 3 dígitos
                    if len(grupo) != 3 or not grupo.isdigit():
                        var_formato = 'brasileiro' if br else 'inglês'
                        raise ValueError(
                            f"Formato inválido '{valor}'. Esperado formato {var_formato} "
                            f"(br={br}): separador de milhar '{sep_milhar}' deve ter "
                            f"exatamente 3 dígitos entre eles."
                        )

    @property
    def val(self) -> Decimal:
        """Retorna o valor Decimal interno."""
        return self._val

    def __str__(self) -> str:
        """Retorna string com 2 casas decimais."""
        return str(self._val)

    def __repr__(self) -> str:
        """Retorna representação oficial do objeto."""
        return f"Moeda('{self._val}')"

    def __add__(self, other: Union['Moeda', int, float, Decimal]) -> 'Moeda':
        """Soma com outra Moeda ou número."""
        if isinstance(other, Moeda):
            return Moeda(self._val + other._val)
        return Moeda(self._val + Decimal(str(other)))

    def __radd__(self, other: Union[int, float, Decimal]) -> 'Moeda':
        """Soma reversa (quando Moeda está à direita)."""
        return self.__add__(other)

    def __sub__(self, other: Union['Moeda', int, float, Decimal]) -> 'Moeda':
        """Subtração com outra Moeda ou número."""
        if isinstance(other, Moeda):
            return Moeda(self._val - other._val)
        return Moeda(self._val - Decimal(str(other)))

    def __rsub__(self, other: Union[int, float, Decimal]) -> 'Moeda':
        """Subtração reversa."""
        return Moeda(Decimal(str(other)) - self._val)

    def __mul__(self, other: Union[int, float, Decimal]) -> 'Moeda':
        """Multiplicação por número."""
        return Moeda(self._val * Decimal(str(other)))

    def __rmul__(self, other: Union[int, float, Decimal]) -> 'Moeda':
        """Multiplicação reversa."""
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float, Decimal]) -> 'Moeda':
        """Divisão por número."""
        return Moeda(self._val / Decimal(str(other)))

    def __rtruediv__(self, other: Union[int, float, Decimal]) -> 'Moeda':
        """Divisão reversa."""
        return Moeda(Decimal(str(other)) / self._val)

    def __neg__(self) -> 'Moeda':
        """Negação unária."""
        return Moeda(-self._val)

    def __pos__(self) -> 'Moeda':
        """Positivo unário."""
        return Moeda(self._val)

    def __eq__(self, other: object) -> bool:
        """Igualdade."""
        if not isinstance(other, Moeda):
            return NotImplemented
        return self._val == other._val

    def __ne__(self, other: object) -> bool:
        """Desigualdade."""
        if not isinstance(other, Moeda):
            return NotImplemented
        return self._val != other._val

    def __lt__(self, other: 'Moeda') -> bool:
        """Menor que."""
        if not isinstance(other, Moeda):
            return NotImplemented
        return self._val < other._val

    def __le__(self, other: 'Moeda') -> bool:
        """Menor ou igual."""
        if not isinstance(other, Moeda):
            return NotImplemented
        return self._val <= other._val

    def __gt__(self, other: 'Moeda') -> bool:
        """Maior que."""
        if not isinstance(other, Moeda):
            return NotImplemented
        return self._val > other._val

    def __ge__(self, other: 'Moeda') -> bool:
        """Maior ou igual."""
        if not isinstance(other, Moeda):
            return NotImplemented
        return self._val >= other._val

    def __hash__(self) -> int:
        """Hash para uso em sets e dicionários."""
        return hash(self._val)

    def __float__(self) -> float:
        """Conversão para float."""
        return float(self._val)

    def __int__(self) -> int:
        """Conversão para int (trunca)."""
        return int(self._val)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)

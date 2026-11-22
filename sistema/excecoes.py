class ErroBiblioteca(Exception):
    pass


class RegistroNaoEncontradoError(ErroBiblioteca):
    pass


class LivroIndisponivelError(ErroBiblioteca):
    pass


class DevolucaoInvalidaError(ErroBiblioteca):
    pass


class DadosInvalidosError(ErroBiblioteca):
    pass

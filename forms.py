from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, IntegerField, FileField, SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional
from config import QUALIFICACOES

# Formulários
class UploadForm(FlaskForm):
    qualificacao = SelectField(
        'Qualificação',
        choices=[('', 'Selecione')] + [(qualificacao, qualificacao) for qualificacao in QUALIFICACOES],
        validators=[DataRequired(message="Selecione uma qualificação.")]
    )
    periodo_de = DateField('Período (de)', validators=[Optional()])
    periodo_ate = DateField('Período (até)', validators=[Optional()])
    horas = IntegerField('Horas', validators=[Optional()])
    quantidade = IntegerField('Quantidade', validators=[Optional()])
    ano_conclusao = IntegerField('Ano de Conclusão', validators=[Optional()])
    ato_normativo = StringField('Ato Normativo', validators=[Optional()])
    tempo = IntegerField('Tempo (anos/meses)', validators=[Optional()])
    certificate = FileField('Certificado', validators=[DataRequired(message="Certificado é obrigatório.")])
    descricao = TextAreaField('Descrição', validators=[Optional()])  # Certifique-se de que este campo foi adicionado
    submit = SubmitField('Enviar')

    def validate(self, **kwargs):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        qualificacoes_com_horas = [
            'Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.',
            'Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.',
            'Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.',
            'Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.'
        ]

        if self.qualificacao.data in qualificacoes_com_horas and not self.horas.data:
            self.horas.errors.append("Este campo é obrigatório para a qualificação selecionada.")
            return False

        return True

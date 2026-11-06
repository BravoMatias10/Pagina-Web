from io import BytesIO
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .scanner import CRITERIA
def pdf(audit):
    output=BytesIO(); styles=getSampleStyleSheet(); flow=[]
    def line(text,style='BodyText'):
        flow.extend([Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style]),Spacer(1,8)])
    line('Audita | Informe de revisión de privacidad','Title')
    line(f'Informe #{audit.pk} · {audit.created:%d/%m/%Y %H:%M %Z}')
    line(audit.url)
    line('Referencia: Ley N° 21.719 de Chile. Entrada en vigencia: 1 de diciembre de 2026. Este informe es una revisión preliminar, no una certificación ni un dictamen jurídico.')
    line('Alcance: HTML inicial de una página, sin ejecutar JavaScript. La ausencia de señales no demuestra incumplimiento. No se inspeccionan bases de datos ni procesos internos.')
    if audit.error: line('Análisis no completado: '+audit.error)
    line('Observaciones automáticas','Heading2')
    for r in audit.results:
        line(r['title'],'Heading3'); line({'observed':'Señal observada','attention':'Atención técnica','review':'Requiere revisión'}[r['status']]); line(r['evidence']); line(r['limit'])
    line('Revisión humana','Heading2')
    for r in audit.reviews.all():
        line(CRITERIA.get(r.criterion,r.criterion),'Heading3'); line(r.get_status_display()); line(r.evidence or 'Sin evidencia registrada.')
    line('Metodología v1 · Evidencia fechada en la creación del informe. Las revisiones manuales reflejan el estado actual al descargar. No se asigna un porcentaje de cumplimiento legal.')
    SimpleDocTemplate(output,title=f'Informe Audita {audit.pk}').build(flow)
    return output.getvalue()

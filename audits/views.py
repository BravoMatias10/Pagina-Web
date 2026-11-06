import logging
import requests
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.cache import cache
from django.db import transaction
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from .models import Audit,Review,Event
from .forms import AuditForm,ReviewForm,SendForm
from .scanner import scan,CRITERIA
from .reports import pdf
logger=logging.getLogger(__name__)
def owned(user):
    return Audit.objects.all() if user.is_staff else Audit.objects.filter(owner=user)
def event(request,action,pk):
    Event.objects.create(actor=request.user,action=action,audit_id_record=pk)
@login_required
def dashboard(request):
    audits=owned(request.user)
    return render(request,'dashboard.html',{'audits':audits[:50],'total':audits.count(),'pending':Review.objects.filter(audit__in=audits,status='pending').count()})
@login_required
def new(request):
    form=AuditForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        from django.conf import settings
        if not settings.SCANNER_ENABLED:
            form.add_error(None,'El analizador está deshabilitado. El operador debe configurar su aislamiento de red antes de habilitarlo.')
            return render(request,'new.html',{'form':form})
        key=f'audit-rate-{request.user.pk}'
        if not cache.add(key,True,60):
            form.add_error(None,'Espera un minuto antes de iniciar otra auditoría.')
        else:
            audit=Audit.objects.create(owner=request.user,url=form.cleaned_data['url'])
            try: audit.results=scan(audit.url)
            except (ValueError,requests.RequestException): audit.error='No se pudo analizar el destino. Comprueba que sea público, accesible y entregue HTML; puede haber un límite de tamaño, tiempo o redirecciones.'
            audit.save()
            Review.objects.bulk_create([Review(audit=audit,criterion=c) for c in CRITERIA])
            event(request,'Auditoría creada',audit.pk)
            return redirect('detail',pk=audit.pk)
    return render(request,'new.html',{'form':form})
@login_required
def detail(request,pk):
    audit=get_object_or_404(owned(request.user),pk=pk)
    FormSet=modelformset_factory(Review,form=ReviewForm,extra=0)
    forms=FormSet(request.POST or None,queryset=audit.reviews.all())
    if request.method=='POST' and forms.is_valid():
        with transaction.atomic():
            forms.save(); event(request,'Revisión manual actualizada',pk)
        messages.success(request,'Revisión guardada. El PDF incluirá estos resultados.')
        return redirect('detail',pk=pk)
    for form in forms: form.criterion_label=CRITERIA[form.instance.criterion]
    return render(request,'detail.html',{'audit':audit,'forms':forms,'send_form':SendForm()})
@login_required
def download(request,pk):
    audit=get_object_or_404(owned(request.user),pk=pk)
    event(request,'PDF descargado',pk)
    response=HttpResponse(pdf(audit),content_type='application/pdf')
    response['Content-Disposition']=f'attachment; filename="audita-{pk}.pdf"'
    response['Cache-Control']='private, no-store'
    return response
@login_required
@require_POST
def send(request,pk):
    audit=get_object_or_404(owned(request.user),pk=pk)
    form=SendForm(request.POST)
    if form.is_valid():
        if not cache.add(f'mail-rate-{request.user.pk}',True,60):
            messages.error(request,'Espera un minuto entre envíos.')
            return redirect('detail',pk=pk)
        mail=EmailMessage(f'Informe de privacidad #{pk}','Adjuntamos la revisión preliminar solicitada. No constituye una certificación legal.',to=[form.cleaned_data['recipient']])
        mail.attach(f'audita-{pk}.pdf',pdf(audit),'application/pdf')
        try:
            mail.send(fail_silently=False)
            from django.conf import settings
            if 'console' in settings.EMAIL_BACKEND:
                messages.info(request,'Modo de desarrollo: correo generado en la consola; no se envió a Internet.')
            else: messages.success(request,'Informe entregado al servidor de correo para su envío.')
            event(request,'Envío de informe solicitado',pk)
        except Exception:
            logger.exception('Error enviando informe %s',pk)
            messages.error(request,'El servidor de correo no pudo procesar el informe.')
    else: messages.error(request,'Revisa el correo y confirma la autorización de envío.')
    return redirect('detail',pk=pk)
@login_required
@require_POST
def delete(request,pk):
    audit=get_object_or_404(owned(request.user),pk=pk)
    event(request,'Auditoría eliminada',pk); audit.delete()
    messages.success(request,'Auditoría y revisiones eliminadas.')
    return redirect('dashboard')
def privacy(request): return render(request,'privacy.html')

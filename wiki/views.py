from labgeeksrpg.wiki.models import Page, RevisionHistory
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime
import diff_match_patch


@login_required
def view_page(request, page_name):
    try:
        page = Page.objects.get(name=page_name)
    except Page.DoesNotExist:
        return render_to_response("create.html", {"page_name": page_name})
    content = page.content
    return render_to_response("view.html", {"page_name": page_name, "content": content, 'request': request, })


@login_required
def edit_page(request, page_name):
    try:
        page = Page.objects.get(name=page_name)
        content = page.content
    except Page.DoesNotExist:
        content = ""
    user = request.user
    c = {}
    c.update(csrf(request))
    if request.method == "POST":
        content = request.POST["content"]
        notes = request.POST["notes"]
        if page:
            page = Page.objects.get(name=page_name)
            page.content = content
        else:
            page = Page(name=page_name, content=content, date=datetime.now(), author=user)
        page.save()
        revision = RevisionHistory.objects.create(page=page, user=user, after=content, date=datetime.now())
        revision.notes = notes
        revision.save()
        return HttpResponseRedirect("/wiki/" + page_name + "/")
    return render_to_response("edit.html", locals(), context_instance=RequestContext(request))


@login_required
def wiki_home(request):
    try:
        PAGES = Page.objects.all()
    except:
        PAGES = None
    return render_to_response('home.html', {'pages': PAGES})


@login_required
def revision_history(request, page_name):
    try:
        page = Page.objects.get(name=page_name)
    except Page.DoesNotExist:
        page = None
    revision_history = []
    dmp = diff_match_patch.diff_match_patch()
    last_rev = ''
    if page:
        revisions = RevisionHistory.objects.filter(page=page).order_by('date')
        for revision in revisions:
            diff = dmp.diff_main(last_rev, revision.after)
            dmp.diff_cleanupSemantic(diff)
            diff_html = dmp.diff_prettyHtml(diff)
            diff_markdown = diff_html.replace("&para;<br>", "\n")
            diff_markdown = diff_markdown.replace("&lt;", "<")
            diff_markdown = diff_markdown.replace("&gt;", ">")
            diff_markdown = diff_markdown.replace("#ffe6e6;", "red")
            diff_markdown = diff_markdown.replace("#e6ffe6;", "green")
            holder = {
                'date': revision.date,
                'notes': revision.notes,
                'user': revision.user,
                'diff': diff_markdown,
                'revised_text': revision.after,
            }
            revision_history.append(holder)
            last_rev = revision.after
    args = {
        'name': page_name,
        'revision_history': revision_history,
        'request': request,
    }
    return render_to_response('revisions.html', args)
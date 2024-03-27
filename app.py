from pathlib import Path

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_jinja2 import render_string, render_template

from models import Todo
from turbo import Turbo
from gabor import ROUTES

app = web.Application()
aiohttp_jinja2.setup(
    app, loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates")
)

turbo = Turbo()

todos = [Todo("buy eggs"), Todo("walk the dog")]


def get_todo_by_id(id: str):
    todo = [todo for todo in todos if todo.id == id]
    if len(todo) == 0:
        raise web.HTTPNotFound()
    return todo[0]


async def index(request: web.Request):
    if request.method == "POST":
        form = await request.post()
        todo = Todo(form["task"])
        todos.append(todo)

        return turbo.stream(
            [
                turbo.append(
                    render_string("_todo.html", request, {"todo": todo}),
                    target="todos",
                ),
                turbo.update(
                    render_string("_todo_input.html", request, {}), target="form"
                ),
            ]
        )

    return render_template("index.html", request, {"todos": todos})


async def toggle(request: web.Request):
    id = request.match_info["id"]
    todo = get_todo_by_id(id)
    todo.completed = not todo.completed

    return turbo.stream(
        turbo.replace(
            render_string("_todo.html", request, {"todo": todo}),
            target=f"todo-{todo.id}",
        )
    )


async def edit(request: web.Request):
    id = request.match_info["id"]
    todo = get_todo_by_id(id)
    if request.method == "POST":
        form = await request.post()
        todo.task = form["task"]
        return turbo.stream(
            turbo.replace(
                render_string("_todo.html", request, {"todo": todo}),
                target=f"todo-{todo.id}",
            )
        )

    return turbo.stream(
        turbo.replace(
            render_string("_todo_edit.html", request, {"todo": todo}),
            target=f"todo-{todo.id}",
        )
    )


async def delete(request: web.Request):
    id = request.match_info["id"]
    todo = get_todo_by_id(id)
    todos.remove(todo)

    return turbo.stream(turbo.remove(f"todo-{id}"))


app.add_routes(
    [
        web.static("/static", Path(__file__).parent / "static", name="static"),
        web.get("/", index, name="index"),
        web.post("/", index, name="index"),
        web.post("/toggle/{id}", toggle, name="toggle"),
        web.get("/edit/{id}", edit, name="edit"),
        web.post("/edit/{id}", edit, name="edit"),
        web.post("/delete/{id}", delete, name="delete"),
    ] + ROUTES
)

web.run_app(app)

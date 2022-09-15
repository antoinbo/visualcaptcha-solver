
import solver

routes = {
    "start": "/start",
    "image": "/image",
    "check": "/try"
}

o = solver.Solver("https://visualcaptcha.example/captcha", routes)
print(o.learn())

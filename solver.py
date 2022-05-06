import hashlib
import requests

class Solver:

    def __init__(self, baseURL, routes):
        self.__s = requests.Session()
        self.__base_url = baseURL
        self.__start_endpoint = routes.get("start")
        self.__image_endpoint = routes.get("image")
        self.__check_endpoint = routes.get("check")

    @staticmethod
    def __check_request(r):
        if r.status_code != 200:
            raise Exception("HTTP status code %d is invalid for request %s %s!" % (r.status_code, r.request.method, r.request.url))

    def requestCaptcha(self, numberOfImages = 0, r = "random"):
        r = self.__s.get(self.__base_url + self.__start_endpoint, data={
            "numberOfImages": numberOfImages,
            "r": r
        })

        self.__check_request(r) # raises an exception if HTTP response status code is not 200

        return r.json() # raises an exception if not JSON

    def requestCaptchaImage(self, index, r = "random"):
        r = self.__s.get(self.__base_url + self.__image_endpoint, data= {
            "index": index,
            "r": r
        })

        self.__check_request(r) # raises an exception if HTTP response status code is not 200

        return r.content

    def requestCheck(self, image):
        r = self.__s.post(self.__base_url + self.__check_endpoint, data={
            "image": image
        })

        self.__check_request(r) # raises an exception if HTTP response status code is not 200

        return r.json() # raises an exception if not JSON (true or false)

    def testMinimumNumberOfImages(self):
        data = self.requestCaptcha(0)

        values = data.get("values") # raises an exception if key does not exist

        return len(values)

    def testMaximumNumberOfImages(self, limit = 10000):
        number = 1

        while number < limit:
            number *= 10
            
            data = self.requestCaptcha(number)

            values = data.get("values") # raises an exception if key does not exist

            if len(values) != number:
                number = len(values)
                break

        return number

    def learn(self, limit=1000):
        print("Learning mode configured for a maximum of %d iterations!" % limit)

        print("Test minimum number of images:")
        minimumNumberOfImages = self.testMinimumNumberOfImages()
        print("\t> Minimum number of images is %d!" % minimumNumberOfImages)

        print("Test maximum number of images:")
        maximumNumberOfImages = self.testMaximumNumberOfImages()
        print("\t> Maximum number of images is %d!" % maximumNumberOfImages)

        found = {}
        guess = {}

        iterationNumber = 0
        while iterationNumber < limit:
            iterationNumber += 1
            print("Iterations number #%d" % iterationNumber)

            print("\t> Request new captcha:")
            data = self.requestCaptcha(minimumNumberOfImages)

            imageName = data.get("imageName")
            imageValues = data.get("values")
            print("\t\t> Image to find: %s" % imageName)

            print("\t> Request captcha images:")
            for i in range(0, len(imageValues)):
                print("\t\t> Download captcha image #%d:" % i)
                image = self.requestCaptchaImage(i)

                imageHash = hashlib.sha256(image).hexdigest()
                print("\t\t\t> Hash: %s" % imageHash)

                imageValues[i].append(imageHash)

            if imageName in found.values():
                print("\t> Image %s found!" % imageName)
                for value in imageValues:
                    i, h = value

                    if found.get(h) == imageName:
                        print("\t> Check %s" % h)
                        if self.requestCheck(i):
                            print("\t> Valid %s!" % h)
                            break
                        else:
                            print("\t> Error %s!" % h)
            else:
                print("\t> Image %s not found!" % imageName)
                best = {}
                for value in imageValues:
                    i, h = value

                    if h not in found:
                        guess[h] = guess.get(h, {})
                        guess[h][imageName] = guess.get(imageName, 0)

                        if guess[h][imageName] >= best.get("value", 0):
                            best = {"i": i, "h": h, "v": guess[h][imageName]}

                print("\t> Check %s" % best["h"])
                if self.requestCheck(best["i"]):
                    print("\t> Valid %s!" % best["h"])
                    del guess[best["h"]]
                    found[best["h"]] = imageName
                else:
                    print("\t> Error %s!" % best["h"])
                    for value in imageValues:
                        i, h = value

                        if h not in found:
                            if h != best["h"]:
                                guess[h][imageName] += 1

            print("%d guess and %d found" % (len(guess), len(found)))
            if len(found) == maximumNumberOfImages:
                print("> All images found!")
                break
        
        print(found)

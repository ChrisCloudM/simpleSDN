import threading


def Multi_threading(func):
    def wrapper(self, **kwargs):
        threadingList = []
        for k, v in kwargs.items():
            threadingList.append(threading.Thread(target=func, args=(self, v), name=k))
        for i in threadingList:
            i.start()
        for j in threadingList:
            j.join()
    return wrapper


class Test:
    @Multi_threading
    def test(self, kwargs):
        print("start")
        print(kwargs)



if __name__ == "__main__":
    a = Test()
    a.test(**{"1":"1", "2":"2"})
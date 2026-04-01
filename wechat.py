from services.wechat_service import *
import time


if __name__ == "__main__":

    # print(get_media())

    digest = input("digest: ")
    
    if digest == "":
        digest = " "

    start = time.time()
    movie_list, title = extract("movie")
    # print(title)
    # print(movie_list)

    movie_list = upload_images(movie_list)

    wechat_html = build_html(movie_list)

    result = upload_to_draft(wechat_html, digest, title)

    print(result)
    print(time.time() - start)

    

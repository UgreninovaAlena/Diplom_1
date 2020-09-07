import requests
import json
import os
import datetime

def catch_request_error(answer, type_reqoest):
  result = {}
  result['error'] = 0
  if answer.status_code < 200 or answer.status_code > 299:
    result['error'] = 1
    if type_reqoest == 'VKGetLinks':
      result['user_massage'] = f'[Получение ссылок для скачивания изображений VK] Ошибка соединения с сервером. Получен ответ сервера: {answer.status_code}'
    elif type_reqoest == 'YanGetLink':
      result['user_massage'] = f'[Получение ссылок для загрузки изображений YaDisk] Ошибка соединения с сервером. Получен ответ сервера: {answer.status_code}'
    elif type_reqoest == 'YanDownloadPhoto':
      result['user_massage'] = f'[Загрузка изображения YaDisk] Ошибка соединения с сервером. Получен ответ сервера: {answer.status_code}'

    return result
  else:
    if type_reqoest == 'VKGetLinks':
      JSONanswer = answer.json()
      if 'error' in JSONanswer.keys():
        result['error'] = 1
        result['error_code'] = JSONanswer['error']['error_code']
        result['error_msg'] = JSONanswer['error']['error_msg']
        result['user_massage'] = f'В ответе сервера получена ошибка: ERROR_CODE = {result["error_code"]} - {result["error_msg"]}'
    elif type_reqoest == 'YanGetLink':
        JSONanswer = answer.json()
        # print('_________')
        # print(JSONanswer)
        # print('_________')
  return result

def find_max_size(photo_size_list):
    photo_size_max = 0
    result_data = {}
    for photo in photo_size_list:
        pixel_count = photo['height'] * photo['width']
        if pixel_count > photo_size_max:
            photo_size_max = pixel_count
            result_data = photo
    return result_data

def get_input_data(filename):
    with open(filename) as f:
        result = json.load(f)
        if result['owner_id'][0] == '0':
            print('ВНИМАНИЕ! Во входных данных [owner_id] будет приведен к типу [int] для дальнейшей работы.')
            print('Содержащиеся в начале строки "0" будут удалены.')
        result['owner_id'] = int(result['owner_id'])
    return result

class DownloadPhotoFromVKInPS():
    URL = 'https://api.vk.com/method/photos.get'


    def __init__(self, AOuthData):
        self.adres_for_save = AOuthData['adres_for_save']
        self.parametrs_photos_get = {
            'lang': 0,
            'owner_id': AOuthData['owner_id'],
            'album_id': 'profile',
            'rev': 0,
            'extended': 1,
            'feed_type': 'photo',
            'photo_sizes': 1,
            'offset': 2,
            'count': AOuthData['count'],
            'access_token': AOuthData['access_token'],
            'v': 5.122
        }
        self.answer = requests.get(url=self.URL, params=self.parametrs_photos_get)
        self.downloadinfo = catch_request_error(self.answer, 'VKGetLinks')
        if self.downloadinfo['error']:
            pass
        else:
          self.downloadinfo['user_massage'] = 'Photos from VK uploaded'
          self.JSONanswer = self.answer.json()
        pass

    def download_photos_on_PC(self):
        list_photos = self.answer.json()['response']['items']
        dtime = str(datetime.datetime.now())
        name_filelog = os.path.join('photos', f'filelog.txt')
        for_log = []
        self.downloads = []

        list_names = {}
        with open(name_filelog, 'a') as filelog:
            for photo in list_photos:
                link_size = find_max_size(photo['sizes'])

                name = f'{str(photo["likes"]["count"])}.jpg'
                if name in list_names.keys():
                  list_names[name] = list_names[name] + 1
                  name = f'{str(photo["likes"]["count"])}' + f'_{list_names[name]}.jpg'
                else:
                  list_names[name] = 1

                loginfo = {"name": name, "size": link_size['type']}
                photo_name = os.path.join('photos', loginfo["name"])
                self.downloads.append(photo_name)

                with open(photo_name, 'wb') as save_photo:
                    data = requests.get(link_size['url'])
                    save_photo.write(data.content)
                for_log.append(loginfo)

            log_dict = {}
            log_dict[dtime] = for_log
            json.dump(log_dict, filelog, indent=2)
        return 0

class YaUploader:
    PREPARE_UPLOAD_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def __init__(self, AOuthData, file_path: str):
        self.TOKEN = AOuthData['YaToken']
        self.headers = {'Accept': 'application/json', 'Authorization': self.TOKEN}
        self.file_path = file_path
        self.put_url = ''
        self.params = {'path': file_path, 'overwrite': 'true'}

    def upload(self):
        result = {}

        response = requests.get(self.PREPARE_UPLOAD_URL, params=self.params, headers=self.headers)
        self.downloadinfo = catch_request_error(response, 'YanGetLink')
        if self.downloadinfo['error']:
          return self.downloadinfo
        else:
          self.put_url = response.json().get('href')
          files = {'file': open(self.file_path, 'rb')}

          response2 = requests.put(self.put_url, files=files, headers=self.headers)
          self.downloadinfo = catch_request_error(response, 'YanDownloadPhoto')
          if self.downloadinfo['error']:
            return self.downloadinfo
          else:
            if response2.status_code == 201:
              self.downloadinfo['user_massage'] = f'[Загрузка изображения YaDisk] Файл {self.file_path} был загружен без ошибок'
            elif response2.status_code == 202:
              self.downloadinfo['user_massage'] = f'[Загрузка изображения YaDisk] Файл принят {self.file_path} сервером, но еще не был перенесен непосредственно в Яндекс.Диск.'
            else:
              self.downloadinfo['user_massage'] = f'[Загрузка изображения YaDisk] {self.file_path} Undifined note'
        return self.downloadinfo


def main():
    print(
        "Входные данные для работы хранятся во вутреннем файле Data.txt. Описание структуры файла находится во внутреннем файле readme.txt. Проверьте входные данные и нажмите любую клавишу для продолжения.")
    input()
    AOuthData = get_input_data('Data.txt')
    VKdownload = DownloadPhotoFromVKInPS(AOuthData)
    if VKdownload.downloadinfo['error']:
      print(VKdownload.downloadinfo['user_massage'])
    else:
      VKdownload.download_photos_on_PC()

      for filename in VKdownload.downloads:
          uploader = YaUploader(AOuthData, filename)
          result = uploader.upload()
          print(result['user_massage'])


main()
# my_list = ['photos/25.jpg','photos/31.jpg']
# AOuthData = get_input_data('Data.txt')
# for filename in my_list:
#     uploader = YaUploader(AOuthData, filename)
#     result = uploader.upload()
#     print(result['user_massage'])
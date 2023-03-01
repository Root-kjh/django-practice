# django_practice

`처음부터 시작하는 Django 데이터 적재` 시리즈 연재를 진행한 repository입니다.

## 목차
1. [Django 프로젝트 생성, 임상연구 데이터 크롤링](https://medium.com/humanscape-tech/처음부터-시작하는-django-데이터-적재-1-a4c9db3647d)
2. [Django command 적용, 크롤링 중 에러 핸들링, django crontab 적용](https://medium.com/humanscape-tech/처음부터-시작하는-django-데이터-적재-2-6cad7c562129)
3. [임상연구 데이터 한글 번역](https://medium.com/humanscape-tech/처음부터-시작하는-django-데이터-적재-3-6b72a98aeeb1)
4. [적재 단계(task) 나누기, 신규 임상연구 적재, 기존 임상연구 업데이트 command 작성](https://medium.com/humanscape-tech/처음부터-시작하는-django-데이터-적재-4-80a87621fdc5)
5. [임상연구 업데이트, 번역 최적화--end](https://medium.com/@june.333/처음부터-시작하는-django-데이터-적재-5-end-bf43b32a60f4)

## 사용법
각 적재 태스크는 django command를 이용해 진행합니다.

1. save all studies: 전체 임상연구를 적재 or 업데이트합니다.

2. save all new studies: 신규 임상연구를 적재합니다.

3. save new original data: 신규 임상연구를 저장합니다(original_data만을 저장하고 convert, translate task는 수행하지 않습니다).

4. update original data: 기존 임상연구를 업데이트합니다(original_data만을 저장하고 convert, translate task는 수행하지 않습니다).

5. convert original data: original_data를 study model에 맞게 변환합니다.    

6. translate study: 영문 임상연구의 한글 번역본을 생성합니다.


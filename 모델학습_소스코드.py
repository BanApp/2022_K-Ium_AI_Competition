# -*- coding: utf-8 -*-
"""모델학습_소스코드.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kfykxLDcxvums8YYHLaAKwYcCfNpyjd0

# 2022년 k-ium 의료인공지능경진대회
##단국대학교 컴퓨터공학과 정민준
###jmj284@gmail.com, 010-9391-0801


#<모델 학습 및 테스트 코드>


##<학습 및 테스트 환경> <br>
본 프로그램은 'Google Colab' 환경에서 작성 되었습니다.<br>
플랫폼: 'Goolge Colab'<br> 
GPU: Tesla T4<br> 
GPU API: cuda<br>
<br>사용한 언어 및 라이브러리는 아래와 같습니다.
<br>

## <언어> <br>

###1. python3
Version: 3.7.14 (default, Sep  8 2022, 00:06:44)<br>
GCC 7.5.0<br>

## <라이브러리> <br>

###1. transformers
Version: 4.23.1<br> 
License: Apache<br>

###2. torch
Version: 1.12.1+cu113<br>
License: BSD-3<br>

###3. tensorflow)<br>
Version: 2.9.2<br>
License: Apache 2.0<br>

###4. keras
Version: 2.9.0<br>
License: Apache 2.0<br>

###5. scikit-learn
Version: 1.0.2<br>
License: new BSD<br>

###6. pandas
Version: 1.3.5<br> 
License: BSD-3-Clause<br>

###7. numpy
Version: 1.21.6<br>
License: BSD<br>

###8. matplotlib
Version: 3.2.2<br> 
License: PSF<br>

## <사전학습모델> 
bert-base-multilingual-cased<br>
License: Apache 2.0

## <참고자료>

1. https://mccormickml.com/2019/07/22/BERT-fine-tuning/

2. https://colab.research.google.com/drive/1tIf0Ugdqg4qT7gcxia3tL7und64Rv1dP#scrollTo=P58qy4--s5_x

3. https://velog.io/@seolini43/일상연애-주제의-한국어-대화-BERT로-이진-분류-모델-만들기파이썬Colab-코드

## 1. Colab 환경 설정
"""

!pip install transformers

import tensorflow as tf
import torch

from transformers import BertTokenizer
from transformers import BertForSequenceClassification, AdamW, BertConfig
from transformers import get_linear_schedule_with_warmup
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from keras_preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

import pandas as pd
from transformers import BertTokenizer
import csv
import numpy as np
import random
import time
import datetime

# GPU 확인하기
n_devices = torch.cuda.device_count()
print(n_devices)

for i in range(n_devices):
    print(torch.cuda.get_device_name(i))

#코랩 환경에서 구글 드라이브 사용시 마운트 필요, 불필요 혹은 오류 발생시 주석 처리 후 실행
from google.colab import drive
drive.mount('/drive')

#라이브러리 버전 확인, 확인 필요시 주석 제거 후 사용

import sys
'''
print(sys.version)
print()
!pip show transformers
print()
!pip show torch
print()
!pip show tensorflow
print()
!pip show keras 
print()
!pip show scikit-learn 
print()
!pip show pandas
print()
!pip show numpy
print()
!pip show matplotlib
'''

"""## 2. Data Set 불러오기"""

import csv

data_path = '/drive/MyDrive/final model_upload/TrainSet _1차.csv'

print("#################<데이터 호출>#################")
print()
print("예시) /drive/MyDrive/final model_upload/TrainSet _1차.csv")
data_path = input("위의 예시와 같이 학습에 이용할 Data Set 파일이 존재하는 디렉토리의 경로를 입력하세요: ")
print()
print("##########################################")
data = pd.read_csv(data_path,encoding="utf-8")

#자료의 컬럼명을 통일시켜 주기
data.columns=['Findings','Conclusion','AcuteInfarction']

#findings 데이터와 Conclusion 데이터를 하나의 column에 합치기
for i in range(len(data)):
    data.Findings[i] = str(data.Findings[i]) + ' ' + str(data.Conclusion[i])

print("데이터 셋 호출 성공!")

#데이터의 쉐입 및 출력 결과 확인
data.shape
data.sample(n=5)

data_shuffled = data.sample(frac=1).reset_index(drop=True) #데이터 랜덤으로 셔플

#train data & test data 설정
x = len(data_shuffled) #0 ~ x 까지 학습 데이터, x~끝 까지 테스트 데이터, x데이터 사용자 임의 설정

print("#################<학습 데이터, 테스트 데이터 범위 지정>#################")
print()
print("현재 데이터의 전체 길이: %d",x)
print("0 ~ x 까지 학습 데이터, x ~ 끝 까지 테스트 데이터, x데이터 사용자 임의 설정")
x = input("데이터의 범위(x)를 입력하세요(-1 입력시 전체 데이터 학습): ")

if x == '-1':
  x = len(data_shuffled)
else:
  x = int(x)   

train = data_shuffled[:x]
test = data_shuffled[x:]

#테스트 및 훈련 데이터의 쉐입 및 출력 결과 확인
print(train.shape)
print(test.shape)

display(train.head())
display(test.head())

"""## 3. Train Set 전처리"""

#BERT 모델에 이용하기 위한 Test Set의 전처리

# CLS, SEP 붙이기 (문장의 시작, 끝 구분)
sentences = ["[CLS] " + str(s) + " [SEP]" for s in train.Findings]

#결과 라벨 할당
labels = train['AcuteInfarction'].values

#사전학습모델 bert-base-multilingual-cased 설치 및 사용, License: Apache 2.0
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased', do_lower_case=False)
tokenized_texts = [tokenizer.tokenize(s) for s in sentences] #토큰화

#print(sentences[0])  #토크나이징 전
#print(tokenized_texts[0]) #토크나이징 후

#시퀀스 설정 및 정수 인덱스 변환 & 패딩
#최대 시퀀스 길이, bert모델의 인식 가능한 최대 길이가 512, 따라서 CLS와 SEP를 빼고 510까지 할당 가능
MAX_LEN = 510
input_ids = [tokenizer.convert_tokens_to_ids(x) for x in tokenized_texts]
input_ids = pad_sequences(input_ids, maxlen=MAX_LEN, dtype="long", truncating="post", padding="post")

# 어텐션 마스크
attention_masks = []
for seq in input_ids:
    seq_mask = [float(i>0) for i in seq]
    attention_masks.append(seq_mask)

#print(attention_masks[0])

# 파이토치 텐서로 변환
train_inputs, validation_inputs, train_labels, validation_labels = train_test_split(input_ids,
                                                                                    labels, 
                                                                                    random_state=2000, 
                                                                                    test_size=0.00001)

train_masks, validation_masks, _, _ = train_test_split(attention_masks, 
                                                       input_ids,
                                                       random_state=2000, 
                                                       test_size=0.00001)

train_inputs = torch.tensor(train_inputs)
train_labels = torch.tensor(train_labels)
train_masks = torch.tensor(train_masks)

validation_inputs = torch.tensor(validation_inputs)
validation_labels = torch.tensor(validation_labels)
validation_masks = torch.tensor(validation_masks)

# 배치 사이즈 설정 및 데이터 설정
batch_size = 16

train_data = TensorDataset(train_inputs, train_masks, train_labels)
train_sampler = RandomSampler(train_data)
train_dataloader = DataLoader(train_data, sampler=train_sampler, batch_size=batch_size)

validation_data = TensorDataset(validation_inputs, validation_masks, validation_labels)
validation_sampler = SequentialSampler(validation_data)
validation_dataloader = DataLoader(validation_data, sampler=validation_sampler, batch_size=batch_size)

"""## 5. 모델 생성"""

#코랩 환경에서 gpu 사용가능 여부를 판별 및 device 할당 위해서 사용

if torch.cuda.is_available():    
    device = torch.device("cuda")
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(0))
else:
    device = torch.device("cpu")
    print('No GPU available, using the CPU instead.')

#코랩 환경에서 gpu 캐시 초기화를 위해서 사용, 필요시 주석 제거하고 사용, 오류 발생시 주석 처리 필요
'''
import torch, gc
gc.collect()
torch.cuda.empty_cache()
'''

#사전학습모델 bert-base-multilingual-cased 설치 및 사용, License: Apache 2.0
model = BertForSequenceClassification.from_pretrained("bert-base-multilingual-cased", num_labels=2)
model.cuda()

# 옵티마이저
optimizer = AdamW(model.parameters(),
                  lr = 2e-5, # 학습률(learning rate)
                  eps = 1e-8 
                )

# 에폭수
epochs = 4

# 총 훈련 스텝 : 배치반복 횟수 * 에폭
total_steps = len(train_dataloader) * epochs

# 스케줄러 생성
scheduler = get_linear_schedule_with_warmup(optimizer, 
                                            num_warmup_steps = 0,
                                            num_training_steps = total_steps)

"""## 6. 모델 학습"""

# 정확도 계산 함수
def flat_accuracy(preds, labels):
    
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()

    return np.sum(pred_flat == labels_flat) / len(labels_flat)
    
    
# 시간 표시 함수
def format_time(elapsed):

    # 반올림
    elapsed_rounded = int(round((elapsed)))
    
    # hh:mm:ss으로 형태 변경
    return str(datetime.timedelta(seconds=elapsed_rounded))

#랜덤시드 고정
seed_val = 42
random.seed(seed_val)
np.random.seed(seed_val)
torch.manual_seed(seed_val)
torch.cuda.manual_seed_all(seed_val)

#그래디언트 초기화
model.zero_grad()

# 학습 # 배치 사이즈 = 16, epoch = 4 
for epoch_i in range(0, epochs):
    
    # ========================================
    #               Training
    # ========================================
    
    print("")
    print('======== Epoch {:} / {:} ========'.format(epoch_i + 1, epochs))
    print('Training...')

    # 시작 시간 설정
    t0 = time.time()

    # 로스 초기화
    total_loss = 0

    # 훈련모드로 변경
    model.train()
        
    # 데이터로더에서 배치만큼 반복하여 가져옴
    for step, batch in enumerate(train_dataloader):
        # 경과 정보 표시
        if step % 500 == 0 and not step == 0:
            elapsed = format_time(time.time() - t0)
            print('  Batch {:>5,}  of  {:>5,}.    Elapsed: {:}.'.format(step, len(train_dataloader), elapsed))

        # 배치를 GPU에 넣음 #배치사이즈 16
        batch = tuple(t.to(device) for t in batch)
        
        # 배치에서 데이터 추출
        b_input_ids, b_input_mask, b_labels = batch

        # Forward 수행                
        outputs = model(b_input_ids,token_type_ids=None,
                        attention_mask=b_input_mask,labels=b_labels)
        
        # 로스 구함
        loss = outputs[0]

        # 총 로스 계산
        total_loss += loss.item()

        # Backward 수행으로 그래디언트 계산
        loss.backward()

        # 그래디언트 클리핑
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        # 그래디언트를 통해 가중치 파라미터 업데이트
        optimizer.step()

        # 스케줄러로 학습률 감소
        scheduler.step()

        # 그래디언트 초기화
        model.zero_grad()

    # 평균 로스 계산
    avg_train_loss = total_loss / len(train_dataloader)            

    print("")
    print("  Average training loss: {0:.2f}".format(avg_train_loss))
    print("  Training epcoh took: {:}".format(format_time(time.time() - t0)))
        
    # ========================================
    #               Validation
    # ========================================

    print("")
    print("Running Validation...")

    #시작 시간 설정
    t0 = time.time()

    # 평가모드로 변경
    model.eval()

    # 변수 초기화
    eval_loss, eval_accuracy = 0, 0
    nb_eval_steps, nb_eval_examples = 0, 0

    # 데이터로더에서 배치만큼 반복하여 가져옴
    for batch in validation_dataloader:
        # 배치를 GPU에 넣음
        batch = tuple(t.to(device) for t in batch)
        
        # 배치에서 데이터 추출
        b_input_ids, b_input_mask, b_labels = batch
        
        # 그래디언트 계산 안함
        with torch.no_grad():     
            # Forward 수행
            outputs = model(b_input_ids, 
                            token_type_ids=None, 
                            attention_mask=b_input_mask)
        
        # 로스 구함
        logits = outputs[0]

        # CPU로 데이터 이동
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()
        
        # 출력 로짓과 라벨을 비교하여 정확도 계산
        tmp_eval_accuracy = flat_accuracy(logits, label_ids)
        eval_accuracy += tmp_eval_accuracy
        nb_eval_steps += 1

    print("  Accuracy: {0:.2f}".format(eval_accuracy/nb_eval_steps))
    print("  Validation took: {:}".format(format_time(time.time() - t0)))

print("")
print("Training complete!")

"""##7. 모델 저장"""

#모델,토크나이저 저장
#s_path 변수에 모델 저장경로 삽입 총 5개의 파일이 저장되어야 함.

s_path = '/drive/MyDrive/submit_model'

print("#################<모델 저장>#################")
print()
print("<경로에 저장 돼야 하는 파일들>")
print("1. config.json")
print("2. pytorch_model.bin")
print("3. special_tokens_map.json")
print("4. tokenizer_config.json")
print("5. vocab.txt")
print()
print("예시) /drive/MyDrive/submit_model")
s_path = input("위의 예시와 같이 학습된 모델을 저장할 디렉토리의 경로를 입력하세요: ")
print()
print("#########################################")

model.save_pretrained(s_path) #모델저장
tokenizer.save_pretrained(s_path) #토크나이저 저장

print("모델 저장 완료!")

"""## 8. 테스트셋 평가"""

#시그모이드
def sigmoid(x): 
    return 1.0/(1 + np.exp(-x))

def flat_accuracy(preds, labels):
    
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()

    return np.sum(pred_flat == labels_flat) / len(labels_flat)

def format_time(elapsed):

    # 반올림
    elapsed_rounded = int(round((elapsed)))
    
    # hh:mm:ss으로 형태 변경
    return str(datetime.timedelta(seconds=elapsed_rounded))


test_ans = [] #모델의 결과 저장
test_prob = [] #가능성 저장

#시작 시간 설정
t0 = time.time()

#테스트셋 데이터 전처리
def convert_input_data(sentences):
    sentences = ["[CLS] " + str(sentences) + " [SEP]"]

    # BERT의 토크나이저로 문장을 토큰으로 분리
    tokenized_texts = [tokenizer.tokenize(sent) for sent in sentences]

    # 입력 토큰의 최대 시퀀스 길이
    MAX_LEN = 509

    # 토큰을 숫자 인덱스로 변환
    input_ids = [tokenizer.convert_tokens_to_ids(x) for x in tokenized_texts]
    
    # 문장을 MAX_LEN 길이에 맞게 자르고, 모자란 부분을 패딩 0으로 채움
    input_ids = pad_sequences(input_ids, maxlen=MAX_LEN, dtype="long", truncating="post", padding="post")

    # 어텐션 마스크 초기화
    attention_masks = []

    # 어텐션 마스크를 패딩이 아니면 1, 패딩이면 0으로 설정
    # 패딩 부분은 BERT 모델에서 어텐션을 수행하지 않아 속도 향상
    for seq in input_ids:
        seq_mask = [float(i>0) for i in seq]
        attention_masks.append(seq_mask)

    # 데이터를 파이토치의 텐서로 변환
    inputs = torch.tensor(input_ids)
    masks = torch.tensor(attention_masks)

    return inputs, masks

#모델 사용
def Determining_Acute_Ischemic_Stroke(sentences):

    # 평가모드로 변경
    model.eval()

    # 문장을 입력 데이터로 변환
    inputs, masks = convert_input_data(sentences)

    # 데이터를 GPU에 넣음
    b_input_ids = inputs.to(device)
    b_input_mask = masks.to(device)
            
    # 그래디언트 계산 안함
    with torch.no_grad():     
        # Forward 수행
        outputs = model(b_input_ids, 
                        token_type_ids=None, 
                        attention_mask=b_input_mask)

    # 로스 구함
    logits = outputs[0]

    # CPU로 데이터 이동
    logits = logits.detach().cpu().numpy()
    
    #시그모이드 함수, 확률 판단
    pred = sigmoid(logits)
    
    #결과 판단
    result = np.argmax(pred)

    return [result,pred]

#이진 분류 결과(0 or 1)이 담길 정답 리스트
test_ans = []

#이진 분류 결과의 확률([0~1,0~1])이 담길 정답 리스트
test_prob = []

#입력 데이터
d = test.Findings
d.reset_index(drop=True, inplace=True)

#실제 정답 
labels = test.AcuteInfarction

for i in range(len(d)):
  #함수 호출, 이진분류 결과는 a, 확률은 p
  a,p = Determining_Acute_Ischemic_Stroke(d[i])
  test_ans.append(a) #결과 값은 test_ans에 저장
  test_prob.append(p) #확률 값은 test_prob에 저장

print("분류에 소요된 시간: {:}".format(format_time(time.time() - t0)))

from sklearn.metrics import roc_curve, roc_auc_score
import matplotlib.pyplot as plt

#probabilty중 정답이 1일 확률이 담길 리스트 
t_prob =[]

print(len(test_prob))

#probabilty중 정답이 1일 확률(model.predict_proba() 와 동일)
for i in test_prob:
  t_prob.append(i[0][1])

# roc_curve 그래프 그리기
fpr, tpr, thresholds = roc_curve(labels, t_prob)

roc = pd.DataFrame({'FPR(Fall-out)': fpr, 'TPRate(Recall)': tpr, 'Threshold': thresholds})

plt.scatter(fpr, tpr)
plt.title('model ROC curve')
plt.xlabel('FPR(Fall-out)')
plt.ylabel('TPR(Recall)');
plt.plot(fpr, tpr, 'r--')

optimal_idx = np.argmax(tpr - fpr)
optimal_threshold = thresholds[optimal_idx]

# 최적의 threshold
#print('idx:',optimal_idx, 'threshold:', optimal_threshold)

# AUC 면적 구하기
auc_score = roc_auc_score(labels, t_prob)
print('AUC Score:',round(auc_score,6))
print()
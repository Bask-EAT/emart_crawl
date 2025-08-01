uvicorn main1:app --reload --port 8420

주요기능

1.categories.json 생성

2.categories.json으로 상품json 추출

3.상품json으로 상품img 추출

4.루트페이지에서 상세 설정 ui 지원

5.ㅇㅇ

```
상품json 추출결과 예시
{
    "id": "0000008486451",
    "category": "Milk_Dairy",
    "product_name": "[한국야쿠르트] 윌 오리지날 150mlX5개",
    "product_address": "https://emart.ssg.com/item/itemView.ssg?itemId=0000008486451&siteNo=6001&salestrNo=2037",
    "original_price": "8000",
    "selling_price": "8000",
    "image_url": "https://sitem.ssgcdn.com/51/64/48/item/0000008486451_i1_290.jpg",
    "quantity": "10ml 당 107원",
    "out_of_stock": "N"
}
```

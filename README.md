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
    "id": "0000008333613",
    "category": "Noodles_CannedGoods",
    "product_name": "[농심] 올리브 짜파게티 (140gx5입)",
    "product_address": "https://emart.ssg.com/item/itemView.ssg?itemId=0000008333613&siteNo=6001&salestrNo=2037",
    "original_price": "5300",
    "selling_price": "4980",
    "image_url": "https://sitem.ssgcdn.com/13/36/33/item/0000008333613_i1_290.jpg",
    "quantity": "100g 당 711원",
    "out_of_stock": "N"
}
```
```
{
    "id": "0000008333613",
    "category": "Noodles_CannedGoods",
    "product_name": "[농심] 올리브 짜파게티 (140gx5입)",
    "product_address": "https://emart.ssg.com/item/itemView.ssg?itemId=0000008333613&siteNo=6001&salestrNo=2037",
    "image_url": "https://sitem.ssgcdn.com/13/36/33/item/0000008333613_i1_290.jpg",
    "quantity": "100g 당 711원",
    "out_of_stock": "N"
}
```
```
{
    "id": "0000008333613",
    "original_price": "5300",
    "selling_price": "4980"
}
```

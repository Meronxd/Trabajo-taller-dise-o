#pragma once
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <atomic>
#include <cstring>
// BLE API del paquete "esp32 by Espressif Systems" 3.x. Un visor a la vez.
static constexpr char SERVICE_ID[] = "b7215800-26f4-49cf-942d-7a1c6f440901";
static constexpr char DATA_ID[] = "b7215801-26f4-49cf-942d-7a1c6f440901";
static BLECharacteristic* bleData = nullptr;
static std::atomic<bool> hasViewer(false), advertiseAgain(false);
class ViewerCallbacks : public BLEServerCallbacks {
 void onConnect(BLEServer*) override { hasViewer.store(true); }
 void onDisconnect(BLEServer*) override { hasViewer.store(false); advertiseAgain.store(true); }
};
static void startViewer(){
 BLEDevice::init("Horometro-UAI");
 BLEServer* srv=BLEDevice::createServer();
 static ViewerCallbacks callbacks;
 srv->setCallbacks(&callbacks);
 BLEService* service=srv->createService(SERVICE_ID);
 bleData=service->createCharacteristic(DATA_ID,
     BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
 bleData->addDescriptor(new BLE2902());
 service->start();
 BLEAdvertising* adv=BLEDevice::getAdvertising();
 adv->addServiceUUID(SERVICE_ID);
 adv->setScanResponse(true);
 BLEDevice::startAdvertising();
}
static void publishViewer(double hours,double next,bool on,bool due){
 if(!bleData) return;
 if(advertiseAgain.exchange(false)) BLEDevice::startAdvertising();
 static_assert(sizeof(double)==8,"Se requiere float64");
 // ESP32-S3 usa little endian. Un paquete coherente de 18 bytes, sin relleno.
 uint8_t packet[18];
 std::memcpy(packet,&hours,8); std::memcpy(packet+8,&next,8);
 packet[16]=on?1:0; packet[17]=due?1:0;
 bleData->setValue(packet,sizeof packet);
 if(hasViewer.load()) bleData->notify();
}

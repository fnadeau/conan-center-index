cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

set(CMAKE_VERBOSE_MAKEFILE ON)

find_package(ads CONFIG REQUIRED)

add_executable(${PROJECT_NAME} example.cpp)

if(${ADS_VERSION} VERSION_LESS 4.0.3)
    set(LIB ads::qtadvanceddocking)
else()
    if(${QT_VERSION} VERSION_LESS 6.0.0)
        find_package(Qt5 REQUIRED Core CONFIG)
        set(LIB ads::qt5advanceddocking Qt5::Core)
    else()
        find_package(Qt6 REQUIRED Core CONFIG)
        set(LIB ads::qt6advanceddocking Qt6::Core)
        target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_17)
    endif()
endif()

target_link_libraries(${PROJECT_NAME} PRIVATE ${LIB})
